# Agentic Honeypot Backend

FastAPI backend for the honeypot service.

## Local run

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Set environment variables (optional):
   - `API_KEY` (default: `hackathon-secret-key`)
   - `REDIS_URL` (preferred), or `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
4. Start the server:
   - `uvicorn main:app --host 0.0.0.0 --port 8000`

## API

- `POST /honeypot`
  - Headers: `x-api-key: <API_KEY>` (if you enable API key verification)
  - Body:
    ```json
    {
      "conversation_id": "abc",
      "message": "Your account is blocked, pay now"
    }
    ```

## Railway deployment

1. Push this repo to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. Add a Redis service (or attach an external Redis).
4. Set environment variables:
   - `REDIS_URL` from the Railway Redis service
   - `API_KEY` (optional)
5. Railway will use the `Procfile` to run the app.

After deploy, the public URL will be available in Railway.
