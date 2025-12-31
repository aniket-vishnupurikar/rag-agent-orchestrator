# RAG-Chat-Agent 🤖

> Enterprise-grade agentic chat service combining **Retrieval-Augmented Generation (RAG)** with intelligent planning, intent classification, and multi-turn conversation management.

## Overview

RAG-Chat-Agent is a production-ready chat API that intelligently decides **when and how** to retrieve external documents to answer user questions. It features:

- ✅ **Intelligent Planning**: Prioritizes document follow-ups, intent tracking, and recovery from unanswered queries
- ✅ **Intent Classification**: Automatically detects user intent (authentication, HR policy, financial insights, etc.)
- ✅ **Smart Retrieval**: Retries with refined queries when initial results are weak
- ✅ **Multi-turn Conversations**: Maintains session state across turns with cached retrieval results
- ✅ **JWT Authentication**: Secure access with user context for ABAC (Attribute-Based Access Control)
- ✅ **Observability**: Comprehensive structured logging, latency tracking, and token estimation
- ✅ **Pluggable LLM Clients**: Support for local models, Hugging Face, and OpenRouter APIs

## Quick Start

### Prerequisites

- Python 3.8+
- pip (or conda)
- External Retrieval Service running on `localhost:8001` (or configurable URL)
- API key for LLM service (OpenRouter, Hugging Face, or local)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RAG-Chat-Agent
   ```

2. **Create a Python virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   ```bash
   # On Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # On Linux/macOS
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```dotenv
   # LLM Configuration (OpenRouter)
   OPENAI_API_KEY=sk-or-v1-<your-api-key>
   OPENAI_API_BASE=https://openrouter.ai/api/v1
   OPENAI_MODEL=mistralai/mistral-7b-instruct
   
   # Retrieval Service
   RETRIEVAL_SERVICE_URL=http://localhost:8001
   
   # JWT Configuration (⚠️ Change in production)
   JWT_SECRET_KEY=dev-secret-key-change-later
   JWT_ALGORITHM=HS256
   
   # Optional: Hugging Face
   HF_API_TOKEN=hf_<your-token>
   
   # Optional: App Metadata
   OPENROUTER_APP_NAME=RAG-Chat-Agent
   OPENROUTER_APP_URL=http://localhost
   ```

6. **Start the API server**
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```

7. **Verify the server is running**
   ```bash
   curl http://localhost:8000/health
   ```
   
   Expected response: `{"status":"ok"}`

## API Usage

### Authentication

All requests require a valid JWT token in the `Authorization` header:

```bash
Authorization: Bearer <your-jwt-token>
```

The JWT token should contain claims:
```json
{
  "sub": "user123",
  "department": "engineering",
  "clearance": 5,
  "projects": ["project-a", "project-b"]
}
```

### Chat Endpoint

**POST** `/chat/message`

#### Request
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "optional-session-123",
    "message": "What is the authentication policy?"
  }'
```

#### Request Body
```json
{
  "session_id": "optional-session-id",  // Omit for new session
  "message": "user question or message"
}
```

#### Response (200 OK)
```json
{
  "session_id": "session-123",
  "messages": [
    {
      "role": "user",
      "content": "What is the authentication policy?"
    },
    {
      "role": "assistant",
      "content": "Based on our company policy documentation, the authentication policy requires..."
    }
  ]
}
```

#### Error Responses
- **401 Unauthorized**: Invalid or missing JWT token
- **500 Internal Server Error**: Server error (check logs)

### Health Check

**GET** `/health`

```bash
curl http://localhost:8000/health
```

Response: `{"status":"ok"}`

## Architecture

### System Components

```
┌─────────────────┐
│  Client App     │
└────────┬────────┘
         │ HTTP + JWT
         ▼
┌─────────────────────────────────────┐
│     FastAPI Server (Port 8000)      │
├─────────────────────────────────────┤
│  1. JWT Verification                │
│  2. Intent Classification           │
│  3. Action Planning                 │
│  4. Orchestration                   │
└────────┬──────────────┬─────────────┘
         │              │
         │ Retrieve     │ Generate
         │ Documents    │ Response
         ▼              ▼
    ┌─────────┐    ┌──────────┐
    │ RAG     │    │ LLM      │
    │ Service │    │ Service  │
    │ (Port   │    │(OpenRouter
    │ 8001)   │    │ /Local)  │
    └─────────┘    └──────────┘
```

### Request Processing Pipeline

1. **JWT Verification** → Extract user context and authorization
2. **Session Loading** → Retrieve chat history and agent state
3. **Intent Classification** → Detect user's underlying intent
4. **Action Planning** → Decide: retrieve documents? respond? chat?
5. **Execution** → Execute planned actions in sequence
6. **Response Generation** → Call LLM with appropriate context
7. **State Persistence** → Cache results for follow-ups
8. **Return** → Send response with full chat history

### Core Modules

#### Agents Module (`src/agents/`)
Implements agentic decision-making:
- **Planner**: Priority-based action selection
- **Intent Classifier**: Pattern-based intent detection
- **Answerability Check**: Determines if retrieved context answers question
- **Follow-up Detection**: Identifies document references
- **Retrieval Retry**: Handles weak results with query refinement

#### API Module (`src/api/`)
REST API layer:
- **Routes**: Chat endpoint with full conversation history
- **Auth**: JWT token verification and user context extraction
- **Session Store**: In-memory session management (Redis-ready)
- **Models**: Request/response validation with Pydantic

#### LLM Module (`src/llm/`)
Language model integration:
- **Multiple Clients**: LocalLLM, HuggingFace, OpenAI-compatible
- **Prompt Builders**: Grounded (with docs) and conversational (pure chat)

#### Retrieval Module (`src/retrieval/`)
External document search:
- **RetrievalClient**: HTTP wrapper around retrieval microservice
- **Automatic Retries**: Refinement strategy for weak results

#### Observability Module (`src/observability/`)
Monitoring and debugging:
- **Structured Logging**: JSON event logs for all significant operations
- **Latency Tracking**: Measure execution time of critical blocks
- **Token Estimation**: Rough token counting for cost tracking

#### Security Module (`src/security/`)
Authentication and authorization:
- **User Context**: Holds attributes for ABAC (Attribute-Based Access Control)

## Planning Logic (Priority-Based)

The agent decides what to do next based on this priority:

| Priority | Condition | Action | Reason |
|----------|-----------|--------|--------|
| 🔴 **1** | User refers to previous docs + cache exists | Respond with cached chunks | Avoid redundant retrieval |
| 🟠 **2** | Previous response was unanswered | Retrieve + Respond | Recovery mechanism |
| 🟡 **3** | Intent exists + cached chunks available | Respond | Reuse cache for same intent |
| 🟢 **4** | Intent exists (no cache) | Retrieve + Respond | Follow intent-based retrieval |
| 🔵 **5** | Query is factual | Retrieve + Respond | Fallback for Q&A |
| ⚪ **6** | Default | Chat | Pure conversational |

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | LLM API key | `sk-or-v1-...` |
| `OPENAI_API_BASE` | LLM endpoint | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | Model name | `mistralai/mistral-7b-instruct` |
| `RETRIEVAL_SERVICE_URL` | Document service URL | `http://localhost:8001` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | JWT signing key | `dev-secret-key-change-later` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `HF_API_TOKEN` | Hugging Face API key | (not set) |
| `OPENROUTER_APP_NAME` | App metadata for OpenRouter | `RAG-Chat-Agent` |
| `OPENROUTER_APP_URL` | App URL for OpenRouter | `http://localhost` |

## Using Different LLM Providers

### Option 1: OpenRouter (Recommended for Development)

```python
# Automatically loaded from environment
client = OpenAICompatibleClient()
response = client.generate(prompt)
```

**Setup**:
1. Get API key from [openrouter.ai](https://openrouter.ai)
2. Set in `.env`: `OPENAI_API_KEY=sk-or-v1-...`

### Option 2: Local Model (GPU-Intensive)

```python
from src.llm.llm_client import LocalLLMClient

client = LocalLLMClient("mistralai/Mistral-7B-Instruct-v0.2")
response = client.generate(prompt)
```

**Requirements**: NVIDIA GPU with 16GB+ VRAM recommended

### Option 3: Hugging Face Inference API

```python
from src.llm.llm_client import HFInferenceClient

client = HFInferenceClient("mistralai/Mistral-7B-Instruct-v0.2")
response = client.generate(prompt)
```

**Setup**:
1. Get API token from [huggingface.co](https://huggingface.co/settings/tokens)
2. Set in `.env`: `HF_API_TOKEN=hf_...`

## Session Management

### Session ID Behavior

- **Omit `session_id`**: Server creates new session
- **Include `session_id`**: Continues existing conversation
- **Response includes**: Full message history (up to 20 messages rolling window)

### Example: Multi-turn Conversation

```bash
# Turn 1: Start new session
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "What is our leave policy?"}'
# Response: {"session_id": "abc-123", "messages": [...]

# Turn 2: Continue conversation
curl -X POST http://localhost:8000/chat/message \
  -H "Authorization: Bearer <token>" \
  -d '{"session_id": "abc-123", "message": "What about parental leave?"}'
# Response: Uses cached retrieval from Turn 1 for follow-up
```

## Intent Classification

The system automatically detects user intent from keywords:

### Intent Categories

| Intent | Keywords |
|--------|----------|
| `authentication_help` | login, password, authentication, reset, access |
| `hr_policy` | probation, leave, policy, employee, hr |
| `financial_insight` | revenue, growth, financial, segment, fiscal |

Once detected, the intent is reused across turns for consistent retrieval behavior.

## Observability & Debugging

### Enable Detailed Logging

Logs are emitted as structured JSON events:

```json
{
  "timestamp": "2025-12-31T12:34:56.789Z",
  "event": "chat.request",
  "payload": {
    "user_id": "user123",
    "session_id": "session-abc",
    "message": "..."
  }
}
```

### Key Events to Monitor

- `chat.request`: User message received
- `agent.plan`: Actions planned (retrieve, respond, chat)
- `retrieval.attempt.start/result`: Document retrieval status
- `answerability.check`: Whether docs sufficiently answer question
- `llm.prompt`: LLM prompt details and preview
- `latency`: Execution time of critical blocks
- `chat.response`: Response generated

### Example: Check Retrieval Performance

```bash
# Watch logs for retrieval attempts
uvicorn src.api.main:app --reload 2>&1 | grep retrieval
```

## Development & Testing

### Running Tests

```bash
pytest tests/ -v
```

### Local Development

1. Activate virtual environment
2. Run with hot-reload:
   ```bash
   uvicorn src.api.main:app --reload --port 8000
   ```
3. View logs in terminal

### Debugging with Print Statements

Add prints in route handlers (they'll appear in console):

```python
# In src/api/chat/chat_routes.py
print(f"DEBUG: Agent state = {agent_state}")
print(f"DEBUG: Plan actions = {[a.type for a in plan.actions]}")
```

## Deployment Considerations

### Security Checklist

- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Enable JWT expiration verification (currently disabled in dev)
- [ ] Use HTTPS for all API communication
- [ ] Store secrets in environment (not in `.env` file)
- [ ] Implement rate limiting to prevent abuse
- [ ] Add request validation and sanitization
- [ ] Audit user access logs

### Production Adjustments

1. **Session Storage**: Replace in-memory `SessionStore` with Redis
   ```python
   # from session_store import SessionStore -> RedisSessionStore
   session_store = RedisSessionStore(redis_url="redis://...")
   ```

2. **Logging**: Send JSON logs to centralized system
   ```python
   # Add handlers for ELK, Datadog, CloudWatch, etc.
   ```

3. **Monitoring**: Set up alerts for:
   - High latency (llm.generate > 5s)
   - Retrieval failures (retrieval.attempt.result with 0 chunks)
   - LLM errors
   - JWT verification failures

4. **Rate Limiting**: Add FastAPI middleware
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

## Troubleshooting

### Problem: 401 Unauthorized

**Cause**: Invalid or missing JWT token

**Solution**:
- Verify `Authorization: Bearer <token>` header is present
- Check token is valid (not expired if expiration enabled)
- Ensure token contains required claims (`sub`, `department`, etc.)

### Problem: "Retrieval service connection failed"

**Cause**: Cannot reach external retrieval service

**Solution**:
- Verify retrieval service is running on configured URL
- Check `RETRIEVAL_SERVICE_URL` environment variable
- Test connectivity: `curl http://localhost:8001/health`

### Problem: "Invalid or expired JWT"

**Cause**: JWT signature mismatch or expiration

**Solution**:
- Verify `JWT_SECRET_KEY` matches token signing key
- Disable expiration in dev (already done in code)
- Use matching `JWT_ALGORITHM` (HS256)

### Problem: LLM timeouts

**Cause**: LLM service is slow or unresponsive

**Solution**:
- Check LLM service status
- Increase timeout in `llm_client.py`: `timeout=30.0`
- Reduce `max_tokens` in prompt generation
- Try different model or provider

### Problem: Weak retrieval results

**Cause**: Documents don't match query well

**Solution**:
- Customize retry strategy in `retrieval_retry.py`
- Adjust `MIN_ACCEPTABLE_SCORE` threshold
- Enhance query expansion logic in `retrieval_planner.py`
- Check document quality in retrieval service

## Project Structure

For detailed file-by-file documentation, see [`PROJECT_STRUCTURE.md`](./PROJECT_STRUCTURE.md).

Quick overview:
- `src/agents/` - Planning and decision logic
- `src/api/` - FastAPI REST API
- `src/llm/` - LLM clients and prompt generation
- `src/retrieval/` - Document retrieval integration
- `src/observability/` - Logging and monitoring
- `src/security/` - Authentication and user context

## Dependencies

### Core Framework
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/ML
- **LangGraph**: Agent orchestration
- **LangChain**: LLM abstractions
- **Transformers**: Hugging Face models
- **Sentence-transformers**: Semantic embeddings

### Auth
- **python-jose**: JWT handling

### Utilities
- **httpx**: HTTP client
- **python-dotenv**: Environment variables

See `requirements.txt` for versions and `pip freeze` for currently installed packages.

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and test thoroughly
3. Commit with clear messages: `git commit -m "Add feature X"`
4. Push and create a Pull Request
5. Ensure all tests pass before merging

### Code Style

- Python 3.8+ syntax
- Follow PEP 8 naming conventions
- Add docstrings to functions
- Use type hints where possible
- Keep functions focused and testable

## Roadmap

- [ ] ML-based intent classification (replace keyword patterns)
- [ ] Vector database integration for semantic similarity
- [ ] Multi-modal support (images, PDFs)
- [ ] Real-time streaming responses
- [ ] Conversation branching and undo
- [ ] A/B testing framework
- [ ] Advanced memory management
- [ ] Multi-language support

## Support & Issues

For bugs, feature requests, or questions:
1. Check existing issues in the repository
2. Create a new issue with:
   - Clear description
   - Steps to reproduce (if bug)
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

## License

[Add your license here]

## Acknowledgments

Built with:
- FastAPI
- LangChain & LangGraph
- OpenRouter / Hugging Face / Local Models
- Pydantic

---

**Last Updated**: December 31, 2025  
**Version**: 1.0.0  
**Status**: Active Development

For questions or support, please open an issue or contact the team.
