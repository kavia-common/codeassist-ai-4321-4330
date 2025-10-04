# Running Backend Tests

Requirements:
- Python 3.10+
- Dependencies installed from requirements.txt

Run tests in non-interactive CI mode:
```bash
pytest -q
```

Notes:
- Tests mock all OpenAI calls via httpx.AsyncClient monkeypatching; no real network requests are made.
- Environment variables are provided via fixtures; no .env is required.
