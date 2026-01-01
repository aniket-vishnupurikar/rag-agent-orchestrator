# src/api/chat/chat_routes.py
from fastapi import APIRouter, Depends

from src.api.dependancies import get_current_user
from src.api.models.request import ChatRequest
from src.api.models.response import ChatResponse, ChatMessage
from src.api.chat.session_store import SessionStore

from src.retrieval.retrieval_client import RetrievalClient
from src.agents.retrieval_planner import build_retrieval_request
from src.agents.planner import build_plan

from src.llm.llm_client import OpenAICompatibleClient
from src.llm.prompt_builder import (
    build_grounded_prompt,
    build_chat_prompt
)

# 🧠 LLM metadata
from src.agents.llm_intent_classifier import classify_intent_llm
from src.agents.llm_answer_mode_classifier import classify_answer_mode_llm

# 🆕 Citation validation
from src.agents.citation_validator import validate_citations

# 🆕 Context relevance judge (for observability only)
from src.agents.llm_context_relevance import judge_context_relevance_llm
from src.agents.llm_query_rewriter import rewrite_query_llm

# === Observability ===
from src.observability.logger import log_event
from src.observability.timer import timed_block


router = APIRouter()
session_store = SessionStore()

retrieval_client = RetrievalClient(base_url="http://localhost:8001")
llm_client = OpenAICompatibleClient()


@router.post("/chat/message", response_model=ChatResponse)
def chat_message(request: ChatRequest, user=Depends(get_current_user)):
    user_id = user.user_id
    session_id = request.session_id

    agent_state = session_store.get_agent_state(user_id, session_id)
    chat_history = session_store.get_session(user_id, session_id)

    # === STATE SNAPSHOT (START) ===
    log_event(
        "state.before_turn",
        {
            "user_id": user_id,
            "session_id": session_id,
            "last_retrieved_chunks_present": bool(
                agent_state.last_retrieved_chunks
            ),
            "num_last_chunks": len(
                agent_state.last_retrieved_chunks or []
            ),
            "history_length": len(chat_history),
        }
    )

    # === USER MESSAGE ===
    log_event(
        "chat.request",
        {
            "user_id": user_id,
            "session_id": session_id,
            "message": request.message
        }
    )

    session_store.append_message(
        user_id,
        session_id,
        ChatMessage(role="user", content=request.message)
    )

    # === LLM METADATA (NON-BLOCKING) ===
    intent_metadata = classify_intent_llm(
        user_query=request.message,
        chat_history=chat_history,
        agent_state=agent_state
    )

    answer_mode = classify_answer_mode_llm(
        user_query=request.message,
        chat_history=chat_history
    )

    session_store.update_agent_state(
        user_id,
        session_id,
        last_intent_metadata=intent_metadata,
        last_answer_mode=answer_mode.value
    )

    log_event(
        "agent.metadata",
        {
            "intent": intent_metadata,
            "answer_mode": answer_mode.value
        }
    )

    # ==========================================================
    # 🧭 PLANNER INPUT OBSERVABILITY
    # ==========================================================
    relevance_decision = None
    if agent_state.last_retrieved_chunks:
        relevance_decision = judge_context_relevance_llm(
            user_query=request.message,
            retrieved_chunks=agent_state.last_retrieved_chunks,
            chat_history=chat_history
        )

    log_event(
        "planner.input",
        {
            "user_message": request.message,
            "has_prior_context": bool(agent_state.last_retrieved_chunks),
            "num_prior_chunks": len(
                agent_state.last_retrieved_chunks or []
            ),
            "history_length": len(chat_history),
            "intent_metadata": agent_state.last_intent_metadata,
            "answer_mode": agent_state.last_answer_mode,
            "context_relevance": relevance_decision,
        }
    )

    # === PLANNING ===
    plan = build_plan(
        user_query=request.message,
        agent_state=agent_state,
        chat_history=chat_history
    )

    log_event(
        "agent.plan",
        {
            "actions": [
                {"type": a.type, "reason": a.reason}
                for a in plan.actions
            ]
        }
    )

    chunks = []
    source_map = {}
    assistant_text = ""

    for step_index, action in enumerate(plan.actions):
        log_event(
            "agent.action.start",
            {
                "step": step_index,
                "type": action.type,
                "reason": action.reason
            }
        )

        if action.type == "retrieve":
            query = rewrite_query_llm(request.message, chat_history)
            retrieval_input = build_retrieval_request(query)


            with timed_block("retrieval.call"):
                chunks = retrieval_client.retrieve(
                    query=retrieval_input.query,
                    top_k=retrieval_input.top_k,
                    jwt_token=user.raw_token
                )

            source_map = {
                c["chunk_id"]: {
                    "doc_id": c.get("doc_id"),
                    "domain": c.get("domain")
                }
                for c in chunks
                if c.get("chunk_id")
            }

            session_store.update_agent_state(
                user_id,
                session_id,
                last_retrieved_chunks=chunks,
                last_source_map=source_map
            )

            log_event(
                "citation.context",
                {
                    "num_sources": len(source_map),
                    "chunk_ids": list(source_map.keys())
                }
            )

        elif action.type == "respond":
            context = chunks or agent_state.last_retrieved_chunks or []
            source_map = (
                source_map
                or agent_state.last_source_map
                or {}
            )

            prompt = build_grounded_prompt(
                user_query=request.message,
                retrieved_chunks=context,
                chat_history=chat_history,
                answer_mode=answer_mode
            )

            with timed_block("llm.generate"):
                assistant_text = llm_client.generate(prompt)

            diagnostics = validate_citations(
                assistant_text,
                source_map
            )

            log_event(
                "citation.validation",
                diagnostics
            )

        elif action.type == "chat":
            prompt = build_chat_prompt(
                user_query=request.message,
                chat_history=chat_history
            )

            with timed_block("llm.generate"):
                assistant_text = llm_client.generate(prompt)

        log_event(
            "agent.action.complete",
            {
                "step": step_index,
                "type": action.type
            }
        )

    # === STORE RESPONSE ===
    session_store.append_message(
        user_id,
        session_id,
        ChatMessage(role="assistant", content=assistant_text)
    )

    log_event(
        "state.after_turn",
        {
            "user_id": user_id,
            "session_id": session_id,
            "last_answer_mode": answer_mode.value,
            "history_length": len(
                session_store.get_session(user_id, session_id)
            )
        }
    )

    return ChatResponse(
        session_id=session_id,
        messages=session_store.get_session(user_id, session_id)
    )
