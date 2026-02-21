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
    blocked: bool = False
    blocked_message: Optional[str] = None
    flagged_match: bool = False


class EmailAnalysisRequest(BaseModel):
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    subject: Optional[str] = None
    message_text: str
    links: List[str] = Field(default_factory=list)


class EmailIndicator(BaseModel):
    key: str
    value: str


class EmailAnalysisResponse(BaseModel):
    is_scam: bool
    confidence: float
    risk: Dict[str, Any]
    scam_type: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    extracted_intelligence: Optional[ExtractedIntelligence] = None
