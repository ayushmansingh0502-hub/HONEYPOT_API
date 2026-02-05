from fastapi import FastAPI, Depends, HTTPException, Body, Request
from fastapi.security import APIKeyHeader
from schemas import ScamAnalysisResponse
from controller import handle_message

app = FastAPI(title="Agentic Honeypot Backend")

API_KEY = "hackathon-secret-key"
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


@app.post("/honeypot", response_model=ScamAnalysisResponse)
async def honeypot(
    request: Request,
    body: dict = Body(default=None),
    api_key: str = Depends(verify_api_key)
):
    # GUVI / tester may send no body → fabricate one
    if not body:
        conversation_id = "guvi-test"
        message = "test message"
    else:
        conversation_id = body.get("conversation_id", "guvi-test")
        message = body.get("message", "test message")

    return handle_message(
        conversation_id=conversation_id,
        message=message,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
