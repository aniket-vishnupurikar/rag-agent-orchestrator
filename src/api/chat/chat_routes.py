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

# === Observability ===
from src.observability.logger import log_event
from src.observability.timer import timed_block


router = APIRouter()
session_store = SessionStore()

retrieval_client = RetrievalClient(base_url="http://localhost:8001")
llm_client = OpenAICompatibleClient()


@router.post("/chat/message", response_model=ChatResponse)
def chat_message(
    request: ChatRequest,
    user=Depends(get_current_user)
):
    user_id = user.user_id
    session_id = request.session_id

    # === LOAD STATE ===
    agent_state = session_store.get_agent_state(user_id, session_id)
    chat_history = session_store.get_session(user_id, session_id)

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
            "history_length": len(chat_history)
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
    assistant_text = ""

    # === EXECUTION ===
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
            retrieval_input = build_retrieval_request(request.message)

            log_event(
                "retrieval.start",
                {
                    "query": retrieval_input.query,
                    "top_k": retrieval_input.top_k
                }
            )

            with timed_block("retrieval.call"):
                chunks = retrieval_client.retrieve(
                    query=retrieval_input.query,
                    top_k=retrieval_input.top_k,
                    jwt_token=user.raw_token
                )

            session_store.update_agent_state(
                user_id,
                session_id,
                last_retrieved_chunks=chunks
            )

            log_event(
                "retrieval.complete",
                {
                    "num_chunks": len(chunks),
                    "doc_ids": list(
                        {c.get("doc_id") for c in chunks}
                    )
                }
            )

        elif action.type == "respond":
            context = chunks or agent_state.last_retrieved_chunks or []

            log_event(
                "respond.context",
                {
                    "using_cached_context": not bool(chunks),
                    "num_chunks": len(context),
                    "history_length": len(chat_history)
                }
            )

            prompt = build_grounded_prompt(
                user_query=request.message,
                retrieved_chunks=context,
                chat_history=chat_history
            )

            with timed_block("llm.generate"):
                assistant_text = llm_client.generate(prompt)

        elif action.type == "chat":
            log_event(
                "chat.mode",
                {
                    "history_length": len(chat_history)
                }
            )

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
        "chat.response",
        {
            "user_id": user_id,
            "session_id": session_id,
            "response_length": len(assistant_text)
        }
    )

    # === STATE SNAPSHOT (END OF TURN) ===
    log_event(
        "state.after_turn",
        {
            "user_id": user_id,
            "session_id": session_id,
            "last_retrieved_chunks_present": bool(
                agent_state.last_retrieved_chunks
            ),
            "num_last_chunks": len(
                agent_state.last_retrieved_chunks or []
            ),
            "history_length": len(
                session_store.get_session(user_id, session_id)
            )
        }
    )

    return ChatResponse(
        session_id=session_id,
        messages=session_store.get_session(user_id, session_id)
    )
