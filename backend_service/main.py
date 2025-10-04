"""HTTPS runner for the FastAPI backend.

Usage:
    python main.py

This starts the FastAPI app over HTTPS on port 3001 using local self-signed certificates:
- Key:  certs/key.pem
- Cert: certs/cert.pem

Notes:
- This file is a thin runner that imports the main FastAPI app from src.api.main:app.
- It adds a simple /api/hello endpoint on the same app instance.
- Existing ASGI entrypoints and uvicorn CLI usage remain intact (e.g., `uvicorn src.api.main:app --reload --port 3001`).
"""
from fastapi import FastAPI
import uvicorn

# Import the existing app instance without altering the src layout
from src.api.main import app as _existing_app

# Alias to conventional name in this module for clarity and uvicorn run
app: FastAPI = _existing_app


# PUBLIC_INTERFACE
@app.get("/api/hello", summary="Hello over HTTPS", tags=["system"])
def read_root():
    """Simple HTTPS test endpoint to verify HTTPS runner works."""
    return {"message": "Hello from FastAPI over HTTPS"}


if __name__ == "__main__":
    # Run the app over HTTPS with local certs
    # We pass the app instance directly to avoid import indirection issues.
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=3001,
        ssl_keyfile="certs/key.pem",
        ssl_certfile="certs/cert.pem",
    )
