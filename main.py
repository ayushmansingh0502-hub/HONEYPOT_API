import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.security import APIKeyHeader
from schemas import MessageRequest, ScamAnalysisResponse
from controller import handle_message

app = FastAPI(title="Agentic Honeypot Backend")

API_KEY = os.getenv("API_KEY", "hackathon-secret-key")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


@app.post(
    "/honeypot",
    response_model=ScamAnalysisResponse,
    # dependencies=[Depends(verify_api_key)]
)
def honeypot(request_body: MessageRequest, request: Request):
    return handle_message(
        conversation_id=request_body.conversation_id,
        message=request_body.message,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )