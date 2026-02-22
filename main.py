from fastapi import FastAPI, Depends, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from collections import defaultdict, deque
from threading import Lock
import logging
import os
import time
from schemas import ScamAnalysisResponse
from controller import handle_message

app = FastAPI(title="Agentic Honeypot Backend")

# Add CORS middleware to allow Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Chrome extensions)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (including x-api-key)
)

API_KEY = os.getenv("API_KEY", "hackathon-secret-key")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("honeypot_api")

_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    with _rate_limit_lock:
        bucket = _rate_limit_buckets[client_ip]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= RATE_LIMIT_REQUESTS:
            return True

        bucket.append(now)
        return False


@app.get("/")
async def root():
    return {"status": "ok", "service": "honeypot", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/honeypot", response_model=ScamAnalysisResponse)
async def honeypot(
    request: Request,
    body: dict = Body(default=None),
    api_key: str = Depends(verify_api_key)
):
    start = time.perf_counter()
    client_ip = _get_client_ip(request)

    if _is_rate_limited(client_ip):
        logger.warning(
            "honeypot_rate_limited ip=%s path=%s method=%s status=429",
            client_ip,
            request.url.path,
            request.method,
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please retry shortly.",
        )

    
    if not body:
        conversation_id = "guvi-test"
        message = "test message"
    else:
        conversation_id = body.get("conversation_id", "guvi-test")
        message = body.get("message", "test message")

    try:
        response = handle_message(
            conversation_id=conversation_id,
            message=message,
            ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        logger.info(
            "honeypot_request_ok ip=%s path=%s method=%s conversation_id=%s status=200 latency_ms=%d",
            client_ip,
            request.url.path,
            request.method,
            conversation_id,
            int((time.perf_counter() - start) * 1000),
        )
        return response
    except Exception:
        logger.exception(
            "honeypot_request_failed ip=%s path=%s method=%s conversation_id=%s status=500 latency_ms=%d",
            client_ip,
            request.url.path,
            request.method,
            conversation_id,
            int((time.perf_counter() - start) * 1000),
        )
        raise HTTPException(status_code=500, detail="Internal processing error. Check service logs for root cause.")


@app.get("/debug/gemini")
async def debug_gemini(api_key: str = Depends(verify_api_key)):
    """Test endpoint to verify Gemini API is working"""
    import google.generativeai as genai
    
    # Check API key
    api_key_value = os.getenv("GOOGLE_AI_STUDIO_KEY", "AIzaSyDZSLIE_x0Zt74tgMWpXjuaz2yJGl-w5v4")
    
    result = {
        "api_key_present": bool(api_key_value),
        "api_key_length": len(api_key_value) if api_key_value else 0,
        "api_key_starts_with": api_key_value[:10] if api_key_value else None,
        "available_models": [],
        "model_test": None,
        "error": None
    }
    
    # List available models
    try:
        genai.configure(api_key=api_key_value)
        models = genai.list_models()
        result["available_models"] = [
            {"name": m.name, "supports_generate_content": "generateContent" in m.supported_generation_methods}
            for m in models
        ]
    except Exception as e:
        result["list_models_error"] = f"{type(e).__name__}: {str(e)}"
    
    # Try to call Gemini
    try:
        # Try first available model that supports generateContent
        for model_info in result["available_models"]:
            if model_info["supports_generate_content"]:
                model = genai.GenerativeModel(model_info["name"])
                response = model.generate_content("Say 'Hello from Gemini!'")
                result["model_test"] = "SUCCESS"
                result["response"] = response.text.strip()
                result["used_model"] = model_info["name"]
                break
        else:
            raise Exception("No models support generateContent")
    except Exception as e:
        result["model_test"] = "FAILED"
        result["error"] = f"{type(e).__name__}: {str(e)}"
    
    return result


@app.get("/admin/flagged-intelligence")
async def get_flagged_intelligence_stats(api_key: str = Depends(verify_api_key)):
    """
    Get statistics on flagged (blacklisted) intelligence.
    This endpoint shows how many UPI IDs, bank accounts, and phishing links
    have been flagged from previous scam conversations.
    """
    from storage import get_flagged_intelligence_stats
    return get_flagged_intelligence_stats()


@app.post("/analyze-email")
async def analyze_email(
    request: Request,
    body: dict = Body(default=None),
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze an email for scams.
    Used by Chrome extension and email clients.
    """
    from schemas import EmailAnalysisRequest
    from email_analyzer import analyze_email as analyze_email_func
    
    start = time.perf_counter()
    client_ip = _get_client_ip(request)
    
    if _is_rate_limited(client_ip):
        logger.warning(
            "email_analyze_rate_limited ip=%s path=%s method=%s status=429",
            client_ip,
            request.url.path,
            request.method,
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please retry shortly.",
        )
    
    try:
        # Parse email data
        if not body:
            raise HTTPException(status_code=400, detail="Missing email data")
        
        email_request = EmailAnalysisRequest(**body)
        
        logger.info(f"📧 Analyzing email from {email_request.from_email}")
        
        # Use email analyzer
        response = analyze_email_func(email_request)
        
        logger.info(
            "email_analyze_ok ip=%s path=%s method=%s from=%s is_scam=%s confidence=%s status=200 latency_ms=%d",
            client_ip,
            request.url.path,
            request.method,
            email_request.from_email,
            response.is_scam,
            response.confidence,
            int((time.perf_counter() - start) * 1000),
        )
        return response
    except Exception:
        logger.exception(
            "email_analyze_failed ip=%s path=%s method=%s status=500 latency_ms=%d",
            client_ip,
            request.url.path,
            request.method,
            int((time.perf_counter() - start) * 1000),
        )
        raise HTTPException(status_code=500, detail="Internal processing error. Check service logs for root cause.")
