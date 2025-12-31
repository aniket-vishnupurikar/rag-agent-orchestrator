# RAG-Chat-Agent: Complete Project Structure & File Documentation

**Project Purpose**: An enterprise-grade agentic chat service that combines retrieval-augmented generation (RAG) with intelligent planning, intent classification, and multi-turn session management.

---

## 🏗️ Directory Structure

```
RAG-Chat-Agent/
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (dev credentials)
├── .gitignore                       # Git ignore rules
├── notebooks/                       # Jupyter notebooks (currently empty)
└── src/                             # Main source code
    ├── agents/                      # Core agent logic & planning
    │   ├── agent_state.py           # Planner state management
    │   ├── answerability.py         # Heuristic for answer sufficiency
    │   ├── decision.py              # Retrieval decision logic
    │   ├── followup_detection.py    # Detect document follow-ups
    │   ├── intent.py                # Intent data structure
    │   ├── intent_classifier.py     # Intent classification patterns
    │   ├── planner.py               # Main planning engine
    │   ├── planner_types.py         # Action & plan type definitions
    │   ├── retrieval_planner.py     # Build retrieval requests
    │   ├── retrieval_retry.py       # Retrieval retry & refinement logic
    │   └── tools.py                 # Retrieval tool input schema
    ├── api/                         # FastAPI REST API
    │   ├── main.py                  # FastAPI app initialization
    │   ├── dependancies.py          # JWT auth dependency injection
    │   ├── auth/
    │   │   └── jwt.py               # JWT token verification
    │   ├── chat/
    │   │   ├── chat_routes.py       # POST /chat/message endpoint
    │   │   └── session_store.py     # In-memory session & state storage
    │   └── models/
    │       ├── request.py           # ChatRequest Pydantic model
    │       └── response.py          # ChatResponse & ChatMessage models
    ├── llm/                         # LLM client & prompt generation
    │   ├── llm_client.py            # Multiple LLM client implementations
    │   └── prompt_builder.py        # Grounded & conversational prompts
    ├── memory/                      # Placeholder for memory features
    ├── observability/               # Logging, timing, token estimation
    │   ├── logger.py                # JSON event logging
    │   ├── timer.py                 # Context manager for latency tracking
    │   └── token_estimator.py       # Rough token count estimation
    ├── retrieval/                   # External retrieval service client
    │   └── retrieval_client.py      # HTTP client to retrieval microservice
    ├── security/                    # Authentication & authorization
    │   └── user_context.py          # Authenticated user attributes
    └── utils/                       # Placeholder for utilities
```

---

## 📋 Detailed File Documentation

### **1. Project Root Files**

#### `requirements.txt`
**Purpose**: Defines all Python package dependencies.

**Key Dependencies**:
- **FastAPI** (`>=0.110`): Web framework for building REST APIs
- **Uvicorn** (`>=0.27`): ASGI server to run FastAPI
- **Pydantic** (`>=2.6`): Data validation & serialization
- **python-jose** (`>=3.3`): JWT token signing & verification
- **LangGraph** (`>=0.0.39`): Agent orchestration framework
- **LangChain** (`>=0.1.12`): LLM chains & utilities
- **Transformers** (`>=4.38`): Hugging Face models (local LLM support)
- **Sentence-transformers** (`>=2.6`): Semantic embeddings for retrieval
- **python-dotenv** (`>=1.0`): Load environment variables

**Usage**: Install dependencies with `pip install -r requirements.txt`

---

#### `.env`
**Purpose**: Contains environment variables for local development.

**Key Variables**:
```
HF_API_TOKEN=hf_...                    # Hugging Face API token
RETRIEVAL_SERVICE_URL=http://localhost:8001  # External retrieval microservice
JWT_SECRET_KEY=dev-secret-key-change-later   # JWT signing secret
JWT_ALGORITHM=HS256                    # JWT algorithm
OPENAI_API_KEY=sk-or-v1-...            # OpenRouter API key
OPENAI_API_BASE=https://openrouter.ai/api/v1  # OpenRouter endpoint
OPENAI_MODEL=mistralai/mistral-7b-instruct    # LLM model name
OPENROUTER_APP_NAME=RAG-Chat-Agent     # App metadata
OPENROUTER_APP_URL=http://localhost    # App metadata
```

---

#### `.gitignore`
**Purpose**: Exclude sensitive files from version control.
- Ignores: `.env` (contains API keys)

---

### **2. Agent System (`src/agents/`)**

#### `agent_state.py`
**Purpose**: Defines the persistent state of an agent across conversation turns.

**Key Data**:
- `goal`: High-level inferred user objective
- `last_intent`: Previously detected user intent
- `last_intent_confidence`: Confidence score (0.0-1.0)
- `last_retrieved_chunks`: Most recent retrieval results (cached)
- `last_retrieved_doc_titles`: Document sources from retrieval
- `last_retrieval_domains`: Document categories
- `unanswered`: Flag if previous response was incomplete
- `follow_up_expected`: Predicts user will ask follow-up

**Usage**: Shared across planning and response generation to maintain conversation context.

---

#### `answerability.py`
**Purpose**: Soft heuristic to determine if retrieved context sufficiently answers the user question.

**Algorithm**:
1. Checks if minimum number of chunks retrieved (default: 2)
2. Tokenizes user query into words
3. For each retrieved chunk, counts token overlap with query
4. Returns `True` if overlap >= 2 chunks

**Impact**: Affects prompt instruction (honest vs speculative answering).

---

#### `decision.py`
**Purpose**: Determines whether retrieval is needed for a message.

**Logic**:
- Returns `True` if message contains `?` (question mark)
- Returns `True` if message contains domain keywords (e.g., "what is", "how does", "authentication", "policy")
- Otherwise returns `False` (use conversational mode)

**Usage**: Planner uses this to decide first action.

---

#### `followup_detection.py`
**Purpose**: Detects if user is referring to previously retrieved documents.

**Patterns Detected**:
- "first document", "that document", "these documents"
- "the documents you referred to"
- "the document you used"

**Impact**: If detected, overrides normal planning to reuse cached `last_retrieved_chunks` instead of fetching new ones.

---

#### `intent.py`
**Purpose**: Data class representing user intent with confidence tracking.

**Key Methods**:
- `reinforce(delta=0.1)`: Increase confidence by delta, capped at 1.0
- `weaken(delta=0.1)`: Decrease confidence by delta, floored at 0.0

**Usage**: Maintains evolving understanding of what user wants across turns.

---

#### `intent_classifier.py`
**Purpose**: Pattern-based intent classification.

**Intent Categories**:
1. `authentication_help`: Keywords = login, password, authentication, reset, access
2. `hr_policy`: Keywords = probation, leave, policy, employee, hr
3. `financial_insight`: Keywords = revenue, growth, financial, segment, fiscal

**Logic**: Scans message for keywords, returns first matching intent or `None`.

**Limitation**: Simplistic keyword matching; could be enhanced with ML.

---

#### `planner_types.py`
**Purpose**: Type definitions for planning actions.

**Key Types**:

`ActionType` = Literal["retrieve", "respond", "chat", "clarify", "attribute"]

- `retrieve`: Fetch documents from retrieval service
- `respond`: Generate grounded answer using retrieved docs
- `chat`: Generate conversational response without retrieval
- `clarify`: Ask user to clarify (not yet implemented)
- `attribute`: Source attribution (not yet implemented)

`AgentAction`: Single action with optional reason
`AgentPlan`: Sequence of actions to execute

---

#### `planner.py`
**Purpose**: Core planning engine that decides action sequence for each turn.

**Priority-Based Logic** (highest to lowest):

1. **Document Follow-up** (HIGHEST): If user refers to previous docs AND cache exists → `respond` with cached chunks
2. **Unanswered Recovery**: If previous response was incomplete → `retrieve` then `respond`
3. **Intent-Based Follow-up**: If intent exists AND cached chunks exist → `respond` (reuse cache)
4. **Intent-Based Fresh Retrieval**: If intent exists (no cache) → `retrieve` then `respond`
5. **Factual Query Fallback**: If query contains factual keywords → `retrieve` then `respond`
6. **Default Chat**: Otherwise → `chat` (pure conversational, no retrieval)

**Output**: `AgentPlan` with ordered list of actions.

---

#### `retrieval_planner.py`
**Purpose**: Constructs retrieval query from user message.

**Function**: `build_retrieval_request(user_message: str) -> RetrievalToolInput`
- Simply wraps user message as query
- Sets `top_k=10` for default result count

**Note**: Deliberately simple; could be enhanced with query expansion/refinement.

---

#### `retrieval_retry.py`
**Purpose**: Handles retry logic for weak retrieval results.

**Key Config**:
- `MAX_RETRIES = 2`: Try up to 3 times (0, 1, 2)
- `MIN_ACCEPTABLE_SCORE = -6.0`: Tuned for this domain

**Retry Strategy**:
- **Attempt 0**: Original query
- **Attempt 1**: Add "documentation" keyword
- **Attempt 2**: Prefix "internal policy"

**Function**: `should_retry(chunks: List[Dict]) -> bool`
- Returns `True` if no chunks OR best chunk score < threshold

---

#### `tools.py`
**Purpose**: Data class for retrieval tool invocation.

**Class**: `RetrievalToolInput`
- `query: str`: Search query
- `top_k: int = 5`: Number of results

---

### **3. API Layer (`src/api/`)**

#### `main.py`
**Purpose**: FastAPI application factory and router initialization.

**Setup**:
- Creates FastAPI app with title "Agentic Chat Service"
- Loads environment variables from `.env`
- Registers chat router from `src/api/chat/chat_routes.py`
- Provides `/health` endpoint for liveness check

**Startup**: `uvicorn src.api.main:app --reload`

---

#### `dependancies.py`
**Purpose**: Dependency injection for JWT authentication.

**Function**: `get_current_user(credentials: HTTPAuthorizationCredentials) -> UserContext`
- Extracts bearer token from `Authorization` header
- Verifies JWT signature using `verify_and_decode_jwt()`
- Extracts user claims (id, department, clearance, projects)
- Returns `UserContext` object
- Raises HTTP 401 on invalid token

**Usage**: Inject as `Depends(get_current_user)` in route handlers.

---

#### `auth/jwt.py`
**Purpose**: JWT token verification and decoding.

**Key Config**:
```python
SECRET_KEY = "dev-secret-key-change-later"  # ⚠️ Change in production
ALGORITHM = "HS256"
```

**Function**: `verify_and_decode_jwt(token: str) -> dict`
- Decodes JWT using SECRET_KEY and ALGORITHM
- Disables expiration verification (dev mode)
- Returns decoded payload (claims)
- Raises `ValueError` on invalid/expired token

**Security Note**: Expiration verification disabled for development; enable in production.

---

#### `chat/chat_routes.py`
**Purpose**: Main chat endpoint handling multi-turn conversations.

**Endpoint**: `POST /chat/message`

**Request**: `ChatRequest`
```python
{
    "session_id": "optional-session-id",  # New session if omitted
    "message": "user query"
}
```

**Response**: `ChatResponse`
```python
{
    "session_id": "session-id",
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
```

**Processing Pipeline**:

1. **Load Session State**
   - Retrieve chat history and agent state from `SessionStore`
   - Log pre-turn state snapshot

2. **Intent Classification**
   - Detect user intent using `classify_intent()`
   - Update agent state if intent found

3. **Planning**
   - Call `build_plan()` to determine actions
   - Log planned actions

4. **Execute Actions**
   - For `retrieve`: Call retrieval service, handle retries, cache results
   - For `respond`: Generate grounded answer using LLM
   - For `chat`: Generate conversational response using LLM
   - Log latency and token estimates

5. **Store Response**
   - Append assistant message to chat history
   - Return session with full message history

**Key Features**:
- Comprehensive event logging for observability
- Automatic retry with query refinement on weak results
- Caching of retrieval results for follow-ups
- Token estimation for monitoring

---

#### `chat/session_store.py`
**Purpose**: In-memory session storage (Redis-ready abstraction).

**Data Structures**:
- `sessions`: Dict[user_id -> Dict[session_id -> List[ChatMessage]]]
- `agent_states`: Dict[(user_id, session_id) -> AgentState]

**Chat History Methods**:
- `get_session(user_id, session_id)`: Retrieve message list
- `append_message()`: Add message, maintain rolling window (default: 20)
- `session_exists()`: Check if session exists

**Agent State Methods**:
- `get_agent_state()`: Retrieve or create default state
- `update_agent_state(**updates)`: Patch state fields

**Intent Methods** (legacy):
- `get_intent()`: Retrieve agent intent
- `set_intent()`: Set new intent with confidence
- `update_intent_confidence()`: Adjust confidence score

**Design**: Scoped by (user_id, session_id) for multi-tenant isolation.

---

#### `models/request.py`
**Purpose**: Request validation schema.

**Class**: `ChatRequest`
- `session_id: Optional[str]`: Client-provided session ID (new session if omitted)
- `message: str`: User input (required)

**Validation**: Pydantic automatic validation.

---

#### `models/response.py`
**Purpose**: Response serialization schemas.

**Classes**:
- `ChatMessage`: Represents single message in conversation
  - `role: str`: "user" or "assistant"
  - `content: str`: Message text
  
- `ChatResponse`: API response
  - `session_id: str`: Session identifier
  - `messages: List[ChatMessage]`: Full conversation history

---

### **4. LLM Integration (`src/llm/`)**

#### `llm_client.py`
**Purpose**: Multiple LLM client implementations for text generation.

**Three Implementations**:

1. **LocalLLMClient**
   - Downloads model from Hugging Face (default: Mistral-7B)
   - Runs inference on local GPU/CPU
   - Pros: Privacy, no API costs
   - Cons: Resource intensive, slow on CPU

   ```python
   client = LocalLLMClient("mistralai/Mistral-7B-Instruct-v0.2")
   response = client.generate(prompt, max_tokens=512)
   ```

2. **HFInferenceClient**
   - Uses Hugging Face Inference API
   - Requires `HF_API_TOKEN` environment variable
   - Pros: Serverless, easy scaling
   - Cons: API costs, network latency

   ```python
   client = HFInferenceClient("mistralai/Mistral-7B-Instruct-v0.2")
   response = client.generate(prompt)
   ```

3. **OpenAICompatibleClient** (Currently Used)
   - Compatible with OpenAI API interface
   - Configured for OpenRouter by default
   - Reads from environment:
     - `OPENAI_API_KEY`: API key
     - `OPENAI_API_BASE`: Endpoint (default: openrouter.ai)
     - `OPENAI_MODEL`: Model name

   ```python
   client = OpenAICompatibleClient()
   response = client.generate(prompt)
   ```

**All clients implement**: `generate(prompt: str) -> str`

---

#### `prompt_builder.py`
**Purpose**: Constructs prompts for LLM based on context.

**Two Prompt Types**:

1. **`build_grounded_prompt()`** - For retrieval-based responses
   - Parameters:
     - `user_query`: Original question
     - `retrieved_chunks`: List of relevant documents
     - `chat_history`: Previous conversation
     - `answerable`: Whether docs sufficiently answer question
   
   - Structure:
     - System context: "You are an enterprise assistant"
     - Chat history: Last 6 messages for context
     - Documentation: Retrieved chunks formatted as [1], [2], etc.
     - Instruction: Conditional instruction based on answerability
       - If answerable: "Answer using documentation, don't invent"
       - If not answerable: "Say explicitly if answer is missing"
     - User question
   
   - Output: Complete prompt ready for LLM

2. **`build_chat_prompt()`** - For pure conversational responses
   - Parameters:
     - `user_query`: User message
     - `chat_history`: Previous messages
   
   - Structure:
     - System: "You are a helpful assistant"
     - History: Last 8 messages
     - User query
   
   - Simpler than grounded prompt (no document context)

---

### **5. Retrieval Integration (`src/retrieval/`)**

#### `retrieval_client.py`
**Purpose**: HTTP client to external retrieval microservice.

**Class**: `RetrievalClient`
- Endpoint: `POST {base_url}/retrieve`
- Default URL: `http://localhost:8001` (configurable via `RETRIEVAL_SERVICE_URL`)

**Method**: `retrieve(query: str, top_k: int, jwt_token: str) -> List[Dict]`

**Request**:
```json
{
    "query": "search query",
    "top_k": 10
}
```

**Response**:
```json
{
    "results": [
        {
            "text": "chunk content",
            "doc_id": "document identifier",
            "domain": "document category",
            "score": -6.5
        },
        ...
    ]
}
```

**Authentication**: Passes JWT token in `Authorization: Bearer {token}` header.

---

### **6. Security (`src/security/`)**

#### `user_context.py`
**Purpose**: Represents authenticated user attributes for ABAC.

**Class**: `UserContext` (frozen dataclass)
- `user_id: str`: Unique user identifier
- `department: str`: User's department/team
- `clearance: int`: Authorization level (0-10)
- `projects: List[str]`: Project IDs user can access
- `raw_token: str`: JWT token (non-persistent, internal use only)

**Usage**: Extracted from JWT claims and passed through dependency injection. Can be used for document-level access control.

---

### **7. Observability (`src/observability/`)**

#### `logger.py`
**Purpose**: Structured event logging for monitoring & debugging.

**Function**: `log_event(event_type: str, payload: dict)`
- Creates structured log entry:
  ```json
  {
      "timestamp": "2025-12-31T12:34:56.789Z",
      "event": "chat.request",
      "payload": { "user_id": "...", "message": "..." }
  }
  ```
- Outputs to standard logger (JSON format)

**Usage**: 
```python
log_event("chat.request", {"user_id": user_id, "message": msg})
```

**Key Events Logged**:
- `state.before_turn`: Pre-turn state snapshot
- `chat.request`: User message received
- `agent.plan`: Planned actions
- `retrieval.attempt.start/result`: Retrieval status
- `answerability.check`: Answer sufficiency
- `llm.prompt`: Prompt details & preview
- `chat.response`: Response generated
- `latency`: Block execution times

---

#### `timer.py`
**Purpose**: Context manager for measuring block execution time.

**Usage**:
```python
with timed_block("llm.generate", {"model": "mistral-7b"}):
    response = llm_client.generate(prompt)
```

**Output**: Logs `latency` event with:
- `block`: Block name
- `ms`: Duration in milliseconds (2 decimal places)
- Extra metadata passed in dict

---

#### `token_estimator.py`
**Purpose**: Rough token count estimation without tokenizer.

**Function**: `estimate_tokens(text: str) -> int`
- Formula: `max(1, len(text) // 4)`
- Assumes ~4 characters per token for English
- Lightweight approximation for monitoring

**Usage**: Monitor prompt/response size without loading tokenizer.

---

### **8. Empty/Placeholder Directories**

- **`src/memory/`**: Planned for memory management features (vector DB, memory retrieval, etc.)
- **`src/utils/`**: Placeholder for utility functions

---

## 🔄 Request Flow Diagram

```
Client Request
    ↓
POST /chat/message (with Bearer JWT)
    ↓
[JWT Verification] (dependancies.py)
    ↓
[Load Session & Agent State] (session_store.py)
    ↓
[Classify User Intent] (intent_classifier.py)
    ↓
[Build Plan] (planner.py) ← Considers:
                            - Document follow-ups
                            - Previous unanswered state
                            - User intent
                            - Query type
    ↓
[Execute Actions in Sequence]:
    ├─ retrieve?
    │   ├─ Call Retrieval Service (retrieval_client.py)
    │   ├─ Retry if weak (retrieval_retry.py)
    │   └─ Cache results in agent_state
    │
    └─ respond or chat?
        ├─ Build prompt (prompt_builder.py)
        │   ├─ With retrieved context (if respond)
        │   └─ Conversational (if chat)
        ├─ Call LLM (llm_client.py)
        └─ Store response
    ↓
[Observability] (logger.py, timer.py, token_estimator.py)
    ↓
[Return ChatResponse] with full conversation history
```

---

## 🚀 How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (or edit `.env`):
   ```bash
   export OPENAI_API_KEY=sk-or-...
   export RETRIEVAL_SERVICE_URL=http://localhost:8001
   ```

3. **Start the API**:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

4. **Test health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```

5. **Send chat request** (requires valid JWT):
   ```bash
   curl -X POST http://localhost:8000/chat/message \
     -H "Authorization: Bearer <valid-jwt>" \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "session-123",
       "message": "What is the authentication policy?"
     }'
   ```

---

## 📊 Architecture Highlights

### **Modular Design**
- **Agents**: Pure logic, no I/O (testable)
- **API**: HTTP layer with dependency injection
- **LLM**: Pluggable client implementations
- **Observability**: Orthogonal concerns
- **Security**: Centralized JWT verification

### **State Management**
- Per-session agent state tracks:
  - User intent and confidence
  - Cached retrieval results for follow-ups
  - Answerability flags for recovery logic

### **Deterministic Planning**
- Priority-based action selection
- No randomness (auditable)
- Clear recovery paths for failed attempts

### **Extensibility**
- Easy to add new intent patterns
- Pluggable LLM clients
- Retry/refinement strategies configurable
- Ready for Redis-backed session store

---

## ⚠️ Development Notes

- **JWT Expiration**: Currently disabled for dev; enable in production
- **Session Storage**: In-memory only; replace with Redis for production
- **API Keys**: `.env` file with hardcoded keys; use secrets manager
- **Token Estimation**: Rough approximation; use proper tokenizer for accuracy
- **Answerability Heuristic**: Simple keyword overlap; could use semantic similarity
- **Intent Classification**: Pattern-based; could be enhanced with ML model

---

## 🔐 Security Considerations

1. Change `JWT_SECRET_KEY` in production
2. Enable JWT expiration verification
3. Use HTTPS for token transmission
4. Implement rate limiting
5. Validate user clearance before retrieval
6. Log access for audit trails
7. Store session data in encrypted cache (Redis + encryption)

---

**Last Updated**: December 31, 2025  
**Project Status**: Active Development
