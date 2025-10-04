from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, TypedDict, Optional, Any
from datetime import datetime
import uuid
import os
import json
import httpx
from pydantic import BaseModel, Field, ValidationError

# NOTE: This backend intentionally uses NO database for the MVP.
# The minimal in-memory store below acts as a placeholder to outline
# how persistence could be introduced later without changing the API
# surface. Keep imports minimal and avoid introducing DB clients here.

# PUBLIC_INTERFACE
def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch environment variable with optional default, returning None if absent and default is None."""
    return os.environ.get(name, default)

def _parse_cors(origins_raw: Optional[str]) -> List[str]:
    if not origins_raw:
        # Default allow localhost:3000 per requirements
        return ["http://localhost:3000"]
    try:
        # Support comma-separated list or JSON array string
        if origins_raw.strip().startswith("["):
            parsed = json.loads(origins_raw)
            return [str(o) for o in parsed]
        return [o.strip() for o in origins_raw.split(",") if o.strip()]
    except Exception:
        # Fallback to permissive single origin if parsing fails
        return ["http://localhost:3000"]

DEFAULT_MODEL = _env("DEFAULT_OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
REQUEST_TIMEOUT = float(_env("REQUEST_TIMEOUT", "30"))
BACKEND_CORS_ORIGINS = _parse_cors(_env("BACKEND_CORS_ORIGINS"))

app = FastAPI(
    title="AI Copilot Backend",
    description="MVP backend with in-memory placeholders for future persistence.",
    version="0.1.0",
    openapi_tags=[
        {"name": "system", "description": "System and health endpoints"},
        {"name": "ai", "description": "AI Copilot endpoints for generation/explanation/debugging"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# In-memory placeholder data structures (no DB)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Pydantic request/response models
# -----------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="User prompt to generate code or text")
    language: Optional[str] = Field(None, description="Preferred programming language context")
    systemPrompt: Optional[str] = Field(None, description="Override system instruction for the model")
    model: Optional[str] = Field(None, description="OpenAI model name override")

class AIResponseUsage(BaseModel):
    prompt_tokens: Optional[int] = Field(None, description="Number of tokens in the prompt")
    completion_tokens: Optional[int] = Field(None, description="Number of tokens in the completion")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")

class GenerateResponse(BaseModel):
    content: str = Field(..., description="Assistant response content")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[AIResponseUsage] = Field(None, description="Usage metadata if available")

class ExplainRequest(BaseModel):
    code: str = Field(..., description="Code snippet to explain")
    language: Optional[str] = Field(None, description="Programming language of the code")
    model: Optional[str] = Field(None, description="OpenAI model name override")
    systemPrompt: Optional[str] = Field(None, description="Override system instruction")

class DebugRequest(BaseModel):
    code: str = Field(..., description="Code snippet to debug")
    language: Optional[str] = Field(None, description="Programming language of the code")
    error: Optional[str] = Field(None, description="Observed error message or stack trace")
    model: Optional[str] = Field(None, description="OpenAI model name override")
    systemPrompt: Optional[str] = Field(None, description="Override system instruction")

class ErrorEnvelope(BaseModel):
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")

class ErrorResponse(BaseModel):
    error: ErrorEnvelope

# -----------------------------------------------------------------------------
# OpenAI client helper
# -----------------------------------------------------------------------------
async def _call_openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail={"error": {"message": "OPENAI_API_KEY not set", "code": "missing_api_key"}})
    use_model = model or DEFAULT_MODEL
    url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": use_model,
        "messages": messages,
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail={"error": {"message": "Upstream timeout from OpenAI", "code": "upstream_timeout"}})
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail={"error": {"message": f"OpenAI connection error: {str(e)}", "code": "upstream_unreachable"}})

    if resp.status_code >= 400:
        # Pass through OpenAI error shape if possible
        try:
            data = resp.json()
            message = data.get("error", {}).get("message") or json.dumps(data)
        except Exception:
            message = resp.text
        raise HTTPException(status_code=502, detail={"error": {"message": f"OpenAI API error: {message}", "code": "upstream_error"}})

    try:
        data = resp.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail={"error": {"message": "Invalid JSON from OpenAI", "code": "invalid_upstream"}})

    return data

def _extract_content_and_usage(openai_resp: Dict[str, Any]) -> Dict[str, Any]:
    choice = (openai_resp.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content")) or ""
    usage_raw = openai_resp.get("usage") or {}
    usage = AIResponseUsage(
        prompt_tokens=usage_raw.get("prompt_tokens"),
        completion_tokens=usage_raw.get("completion_tokens"),
        total_tokens=usage_raw.get("total_tokens"),
    )
    model_used = openai_resp.get("model") or DEFAULT_MODEL
    return {"content": content, "usage": usage, "model": model_used}

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/", summary="Health Check", tags=["system"])
def health_check():
    """Basic health endpoint to verify the service is running."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post(
    "/generate",
    response_model=GenerateResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Generate content",
    description="Generates code or text using the OpenAI Chat Completions API based on the provided prompt and optional language/system context.",
    tags=["ai"],
)
async def generate(req: GenerateRequest) -> GenerateResponse:
    """Generate content using the provided prompt."""
    system_text = req.systemPrompt or "You are an AI coding copilot. Provide concise, accurate, and developer-friendly output."
    if req.language:
        system_text += f" Where relevant, prefer examples in {req.language}."

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": req.prompt},
    ]

    try:
        raw = await _call_openai_chat(messages, model=req.model)
        parsed = _extract_content_and_usage(raw)
        return GenerateResponse(content=parsed["content"], model=parsed["model"], usage=parsed["usage"])
    except HTTPException:
        raise
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail={"error": {"message": str(ve), "code": "validation_error"}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"message": f"Unexpected error: {str(e)}", "code": "unexpected"}})

# PUBLIC_INTERFACE
@app.post(
    "/explain",
    response_model=GenerateResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Explain code",
    description="Explains the provided code snippet in clear terms, with optional language and system prompts.",
    tags=["ai"],
)
async def explain(req: ExplainRequest) -> GenerateResponse:
    """Explain the provided code snippet."""
    system_text = req.systemPrompt or "You are an expert code explainer. Provide clear, concise explanations and note complexity or pitfalls."
    if req.language:
        system_text += f" The code language is {req.language}."

    user_prompt = f"Explain the following code:\n\n```{req.language or ''}\n{req.code}\n```"

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await _call_openai_chat(messages, model=req.model)
        parsed = _extract_content_and_usage(raw)
        return GenerateResponse(content=parsed["content"], model=parsed["model"], usage=parsed["usage"])
    except HTTPException:
        raise
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail={"error": {"message": str(ve), "code": "validation_error"}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"message": f"Unexpected error: {str(e)}", "code": "unexpected"}})

# PUBLIC_INTERFACE
@app.post(
    "/debug",
    response_model=GenerateResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 504: {"model": ErrorResponse}},
    summary="Debug code",
    description="Provides debugging steps and suggestions for the given code snippet and optional error message.",
    tags=["ai"],
)
async def debug(req: DebugRequest) -> GenerateResponse:
    """Debug the provided code snippet and produce steps/suggestions."""
    system_text = req.systemPrompt or "You are a senior software engineer specializing in debugging. Provide actionable steps and likely causes."
    if req.language:
        system_text += f" Focus on {req.language} specifics where applicable."

    user_prompt = "Analyze and debug the following code."
    if req.error:
        user_prompt += f"\nObserved error:\n{req.error}\n"
    user_prompt += f"\nCode:\n```{req.language or ''}\n{req.code}\n```"

    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw = await _call_openai_chat(messages, model=req.model)
        parsed = _extract_content_and_usage(raw)
        return GenerateResponse(content=parsed["content"], model=parsed["model"], usage=parsed["usage"])
    except HTTPException:
        raise
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail={"error": {"message": str(ve), "code": "validation_error"}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"message": f"Unexpected error: {str(e)}", "code": "unexpected"}})
