from pathlib import Path

def test_generate_openapi(tmp_path, monkeypatch):
    # Ensure interfaces dir is created relative to CWD; run in temp dir to avoid polluting repo
    monkeypatch.chdir(tmp_path)
    from src.api.generate_openapi import generate
    output_path = generate()
    assert output_path.endswith("interfaces/openapi.json")
    p = Path(output_path)
    assert p.exists()
    text = p.read_text()
    assert '"openapi"' in text
    assert '"paths"' in text
