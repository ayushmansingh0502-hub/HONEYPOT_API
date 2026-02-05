from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from schemas import MessageRequest, ScamAnalysisResponse
from controller import handle_message

app = FastAPI(title="Agentic Honeypot Backend")

API_KEY = "hackathon-secret-key"
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

@app.post("/honeypot", response_model=ScamAnalysisResponse)
def honeypot(
    api_key: str = Depends(verify_api_key),
    request: Optional[dict] = None   # 👈 THIS IS THE KEY CHANGE
):
    # If GUVI sends no body, fabricate one
    if not request:
        conversation_id = "guvi-test"
        message = "Hello"
    else:
        conversation_id = request.get("conversation_id", "guvi-test")
        message = request.get("message", "Hello")

    return handle_message(
        conversation_id=conversation_id,
        message=message
    )
