from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MessageRequest(BaseModel):
    conversation_id: Optional[str] = "guvi_test"
    message: Optional[str] = "ping"

class ExtractedIntelligence(BaseModel):
    upi_ids: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)
    phishing_links: List[str] = Field(default_factory=list)

class ScamAnalysisResponse(BaseModel):
    is_scam: bool
    scam_type: Optional[str]
    extracted_intelligence: Optional[ExtractedIntelligence]
    confidence: float
    honeypot_reply: str
    risk: Optional[Dict[str, Any]] = None