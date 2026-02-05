from fastapi import FastAPI, Depends
from fastapi.security import APIKeyHeader
from fastapi import HTTPException
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
    request: MessageRequest = MessageRequest(),
    api_key: str = Depends(verify_api_key)
):
    return handle_message(
        conversation_id=request.conversation_id,
        message=request.message
    )
