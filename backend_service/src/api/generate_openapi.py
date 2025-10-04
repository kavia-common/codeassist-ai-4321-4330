import json
import os

from src.api.main import app

# PUBLIC_INTERFACE
def generate() -> str:
    """Generate the OpenAPI schema JSON for the FastAPI app and write it to interfaces/openapi.json."""
    openapi_schema = app.openapi()
    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    return output_path

def main() -> None:
    """
    Generate the OpenAPI schema JSON for the FastAPI app and write it to interfaces/openapi.json.
    This script is intended to be run with: python -m src.api.generate_openapi
    """
    path = generate()
    print(f"Wrote OpenAPI schema to {path}")

if __name__ == "__main__":
    main()
