from typing import NamedTuple
import re
from schemas import ExtractedIntelligence


class DetectionResult(NamedTuple):
    is_scam: bool
    confidence: float


def detect_scam(message: str) -> DetectionResult:
    """
    Dummy scam detection logic.
    """
    scam_keywords = ["pay", "upi", "urgent", "verify", "account", "http", "www", "link"]

    score = sum(1 for word in scam_keywords if word in message.lower())
    confidence = min(score / len(scam_keywords), 1.0)

    return DetectionResult(
        is_scam=confidence > 0.3,
        confidence=confidence
    )


def extract_intelligence(message: str) -> ExtractedIntelligence:
    """
    Dummy intelligence extraction logic.
    """
    intelligence = ExtractedIntelligence()

    if "@upi" in message:
        intelligence.upi_ids.append("detected@upi")

    links = []

    links.extend(re.findall(r"https?://[^\s)\]}>\"']+", message))
    links.extend(re.findall(r"\bwww\.[^\s)\]}>\"']+", message, flags=re.IGNORECASE))
    links.extend(
        re.findall(
            r"\b[a-zA-Z0-9.-]+\.(?:com|in|net|org|io|co|xyz|biz|info)(?:/[^\s)\]}>\"']*)?",
            message,
            flags=re.IGNORECASE,
        )
    )

    if links:
        seen = set()
        for link in links:
            if "@" in link:
                continue
            if link.lower() in seen:
                continue
            seen.add(link.lower())
            intelligence.phishing_links.append(link)

    return intelligence