from src.api.main import _parse_cors, _extract_content_and_usage, AIResponseUsage

def test_parse_cors_none_defaults():
    origins = _parse_cors(None)
    assert "http://localhost:3000" in origins

def test_parse_cors_csv():
    raw = "http://a.com, http://b.com ,"
    origins = _parse_cors(raw)
    assert origins == ["http://a.com", "http://b.com"]

def test_parse_cors_json_array():
    raw = '["https://x", "http://y"]'
    origins = _parse_cors(raw)
    assert origins == ["https://x", "http://y"]

def test_extract_content_and_usage_happy():
    openai_resp = {
        "model": "mock-model",
        "choices": [
            {"message": {"content": "Result content"}}
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}
    }
    parsed = _extract_content_and_usage(openai_resp)
    assert parsed["content"] == "Result content"
    assert isinstance(parsed["usage"], AIResponseUsage)
    assert parsed["usage"].prompt_tokens == 1
    assert parsed["model"] == "mock-model"

def test_extract_content_and_usage_missing_fields():
    openai_resp = {}
    parsed = _extract_content_and_usage(openai_resp)
    assert parsed["content"] == ""  # defaults empty
    assert isinstance(parsed["usage"], AIResponseUsage)
    assert parsed["model"]  # falls back to default model
