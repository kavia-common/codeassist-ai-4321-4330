import os
import json
import pytest
from fastapi.testclient import TestClient

# Ensure environment variables are set for tests and prevent real network usage.
@pytest.fixture(autouse=True)
def _env_setup(monkeypatch):
    monkeypatch.setenv("DEFAULT_OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")  # dummy value so backend doesn't 500 for missing key
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("REQUEST_TIMEOUT", "2")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["http://localhost:3000"]')
    yield


@pytest.fixture
def app_client():
    # Import here so env setup above is effective
    from src.api.main import app
    client = TestClient(app)
    return client


@pytest.fixture
def openai_success_response():
    return {
        "id": "chatcmpl_test",
        "object": "chat.completion",
        "created": 1710000000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello from mock!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
    }


@pytest.fixture
def openai_error_response():
    return {
        "error": {
            "message": "Model overloaded",
            "type": "server_error"
        }
    }


class _DummyHTTPXResponse:
    def __init__(self, status_code=200, json_data=None, text_data=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text_data
        self._headers = {"content-type": "application/json"} if json_data is not None else {}

    def json(self):
        if self._json_data is None:
            raise json.JSONDecodeError("No json", "", 0)
        return self._json_data

    @property
    def headers(self):
        return self._headers


@pytest.fixture
def mock_openai(monkeypatch, openai_success_response):
    """
    Monkeypatch httpx.AsyncClient.post to avoid real network calls.
    Returns a function that allows customizing the next response.
    """
    import httpx

    state = {"response": _DummyHTTPXResponse(200, json_data=openai_success_response)}

    class _DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):
            return state["response"]

    def set_response(resp):
        state["response"] = resp

    monkeypatch.setattr(httpx, "AsyncClient", _DummyAsyncClient)
    return set_response
