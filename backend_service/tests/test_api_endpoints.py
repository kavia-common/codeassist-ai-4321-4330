import pytest

def test_health_check(app_client):
    r = app_client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "Healthy"

@pytest.mark.asyncio
async def test_generate_success(app_client, mock_openai, openai_success_response):
    # Use default mocked successful OpenAI response
    r = app_client.post("/generate", json={"prompt": "Say hello"})
    assert r.status_code == 200
    data = r.json()
    assert "content" in data and data["content"] == "Hello from mock!"
    assert "model" in data and data["model"] == "gpt-4o-mini"
    assert data.get("usage", {}).get("total_tokens") == 9

@pytest.mark.asyncio
async def test_explain_success(app_client):
    r = app_client.post("/explain", json={"code": "const x = 1;"})
    assert r.status_code == 200
    data = r.json()
    assert "content" in data
    assert "model" in data

@pytest.mark.asyncio
async def test_debug_success(app_client):
    r = app_client.post("/debug", json={"code": "function f(){}"})
    assert r.status_code == 200
    data = r.json()
    assert "content" in data
    assert "model" in data

def test_generate_validation_error(app_client):
    # Missing prompt
    r = app_client.post("/generate", json={})
    assert r.status_code == 422  # FastAPI validation kicks in

def test_explain_validation_error(app_client):
    r = app_client.post("/explain", json={})
    assert r.status_code == 422

def test_debug_validation_error(app_client):
    r = app_client.post("/debug", json={})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_upstream_error_passthrough_as_502(app_client, mock_openai, openai_error_response):
    # Configure mock to return non-2xx with an error body
    from tests.conftest import _DummyHTTPXResponse
    mock_openai(_DummyHTTPXResponse(status_code=500, json_data=openai_error_response))
    r = app_client.post("/generate", json={"prompt": "Hello"})
    assert r.status_code == 502
    data = r.json()
    assert data["detail"]["error"]["code"] == "upstream_error"

@pytest.mark.asyncio
async def test_upstream_invalid_json_returns_502(app_client, mock_openai):
    from tests.conftest import _DummyHTTPXResponse
    # No JSON, only text -> causes JSONDecodeError during parsing
    mock_openai(_DummyHTTPXResponse(status_code=200, json_data=None, text_data="not json"))
    r = app_client.post("/generate", json={"prompt": "Hello"})
    assert r.status_code == 502
    data = r.json()
    assert data["detail"]["error"]["code"] == "invalid_upstream"

@pytest.mark.asyncio
async def test_missing_api_key_returns_500(app_client, monkeypatch):
    # Unset API key to trigger 500 from _call_openai_chat guard
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    r = app_client.post("/generate", json={"prompt": "Hi"})
    assert r.status_code == 500
    data = r.json()
    assert data["detail"]["error"]["code"] == "missing_api_key"
