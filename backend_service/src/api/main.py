from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, TypedDict, Optional
from datetime import datetime
import uuid

# NOTE: This backend intentionally uses NO database for the MVP.
# The minimal in-memory store below acts as a placeholder to outline
# how persistence could be introduced later without changing the API
# surface. Keep imports minimal and avoid introducing DB clients here.

app = FastAPI(
    title="AI Copilot Backend",
    description="MVP backend with in-memory placeholders for future persistence.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP simplicity; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# In-memory placeholder data structures
# -----------------------------------------------------------------------------
# These data structures simulate persistence for conversations and messages.
# They are NOT durable and are reset on process restart.
#
# Future persistence hooks:
# - Replace these dictionaries with repository implementations that talk to a DB.
# - Repositories should expose CRUD methods and be injected into route handlers.
# - See "repositories" inline TODO hints for extension points.

class Message(TypedDict):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str  # ISO 8601

class Conversation(TypedDict):
    id: str
    created_at: str  # ISO 8601
    title: Optional[str]

# Simple in-memory stores
_CONVERSATIONS: Dict[str, Conversation] = {}
_MESSAGES: Dict[str, List[Message]] = {}

# Utilities to manipulate in-memory store
def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _new_id() -> str:
    return uuid.uuid4().hex

# PUBLIC_INTERFACE
def create_conversation(title: Optional[str] = None) -> Conversation:
    """Create a new in-memory conversation placeholder."""
    conv_id = _new_id()
    convo: Conversation = {"id": conv_id, "created_at": _now_iso(), "title": title}
    _CONVERSATIONS[conv_id] = convo
    _MESSAGES[conv_id] = []
    return convo

# PUBLIC_INTERFACE
def append_message(conversation_id: str, role: str, content: str) -> Message:
    """Append a message to an in-memory conversation placeholder."""
    msg: Message = {
        "id": _new_id(),
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "created_at": _now_iso(),
    }
    _MESSAGES.setdefault(conversation_id, []).append(msg)
    return msg

# PUBLIC_INTERFACE
def list_messages(conversation_id: str) -> List[Message]:
    """List messages for a conversation from the in-memory placeholder."""
    return list(_MESSAGES.get(conversation_id, []))

# TODO(repositories): When adding a real database, encapsulate the above
# functions into repository classes (e.g., ConversationRepository, MessageRepository)
# with methods like create(), add_message(), list_messages(), etc. Inject those
# repositories into route handlers via FastAPI dependencies.

@app.get("/", summary="Health Check", tags=["system"])
def health_check():
    """Basic health endpoint to verify the service is running."""
    return {"message": "Healthy"}
