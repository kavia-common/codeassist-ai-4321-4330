# Backend Service - AI Copilot (MVP)

This backend is a FastAPI service that powers the AI Copilot. For the MVP, it intentionally omits a real database. Instead, it uses simple in-memory placeholders to illustrate where persistence would be integrated later.

Why no DB in MVP:
- Simplifies deployment and iteration speed.
- Avoids managing migrations/infrastructure while core features are developed.
- Keeps the codebase lean and focused on API behavior.

Current approach:
- In-memory structures live in `src/api/main.py` and provide:
  - Conversations: minimal metadata in a dictionary keyed by conversation ID.
  - Messages: lists keyed by conversation ID.
- Data is lost on process restart (non-durable, not for production).

Extension points (persistence hooks):
- Introduce repository classes (e.g., `ConversationRepository`, `MessageRepository`) that encapsulate CRUD operations.
- Implement repositories against your chosen database (e.g., Postgres, MySQL, SQLite, MongoDB).
- Inject repositories into routes using FastAPI dependencies to avoid direct imports in handlers.
- Replace in-memory helpers (`create_conversation`, `append_message`, `list_messages`) with repository methods without changing route signatures.

Suggested future schema:
- conversations
  - id (string/uuid)
  - created_at (timestamp)
  - title (string, nullable)
- messages
  - id (string/uuid)
  - conversation_id (string/uuid, FK to conversations.id)
  - role (string: "user" | "assistant" | "system")
  - content (text)
  - created_at (timestamp)

Migration strategy (later):
- Start with a single Alembic migration (SQL DB) or collection definitions (NoSQL).
- Add indices on messages.conversation_id and created_at for efficient retrieval.
- Consider soft deletion fields if needed.

Notes:
- Keep imports minimal in `main.py`. Do not introduce DB clients here.
- For production, add proper CORS restrictions, auth, rate limiting, and observability.

## Environment Variables

Set these in your environment (via .env managed by the orchestrator):

- OPENAI_API_KEY: Required. Your OpenAI API key.
- OPENAI_BASE_URL: Optional. Defaults to https://api.openai.com/v1. Useful for compatible gateways.
- DEFAULT_OPENAI_MODEL: Optional. Defaults to gpt-4o-mini.
- REQUEST_TIMEOUT: Optional. HTTP timeout in seconds (float). Defaults to 30.
- BACKEND_CORS_ORIGINS: Optional. Comma-separated list or JSON array of allowed origins (e.g., "http://localhost:3000,http://127.0.0.1:3000"). If not set, defaults to ["http://localhost:3000", "http://127.0.0.1:3000"] in development.

## CORS

CORS is configured via FastAPI CORSMiddleware:
- If BACKEND_CORS_ORIGINS is set, its values are used.
- If not set, the service allows http://localhost:3000 and http://127.0.0.1:3000 for development convenience.
- Credentials, all methods, and all headers are allowed.

## Development

- Generate OpenAPI JSON:
  - Programmatic: from Python: 
    - `from src.api.generate_openapi import generate; print(generate())`
  - CLI: 
    - `python -m src.api.generate_openapi`
- Run with uvicorn: `uvicorn src.api.main:app --reload --port 3001`

## OpenAI Usage Notes

The service uses httpx to call the Chat Completions endpoint:
- Authorization via `OPENAI_API_KEY` header (Bearer).
- Base URL configurable via `OPENAI_BASE_URL`.
- Default model via `DEFAULT_OPENAI_MODEL`; can be overridden per-request.

Errors from upstream are mapped to appropriate HTTP errors (502/504) with a small error envelope.

