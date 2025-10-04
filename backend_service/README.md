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

Development
- Generate OpenAPI JSON: `python -m src.api.generate_openapi`
- Run with uvicorn: `uvicorn src.api.main:app --reload --port 3001`
