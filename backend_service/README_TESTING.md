# Backend Testing (FastAPI)

- Install dependencies:
  pip install -r requirements.txt

- Run tests (non-interactive):
  pytest -q

Notes:
- External OpenAI calls are mocked; no network calls are made.
- No .env is required during tests; fixtures provide necessary env vars.
