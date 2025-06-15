import os
from dotenv import load_dotenv
import uvicorn

def main():
    # Load environment variables from .env.local file for local development
    # In production, this will be handled differently (e.g., by Docker's --env-file flag)
    load_dotenv(dotenv_path=".env.local")

    print("Starting Secretary Agent (Local Development)...")

    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "0.0.0.0")

    uvicorn.run("src.telegram:app", host=HOST, port=PORT, reload=True)


if __name__ == "__main__":
    main() 