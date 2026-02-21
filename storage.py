import json
import os
import redis
import logging
from lifecycle import ScamPhase
from typing import Optional, Dict, List

logger = logging.getLogger("honeypot.storage")

# In-memory fallback store so the API still works if Redis is unavailable.
_memory_store: dict[str, str] = {}
_flagged_upi_ids = set()
_flagged_bank_accounts = set()
_flagged_phishing_links = set()


def _build_redis_client():
    redis_url = os.getenv("REDIS_URL", "rediss://default:AUp0AAIncDEyODg1YWI2Yzk0ZGY0NThlOWUyNDBjZDQxNDMwZGM2MnAxMTkwNjA@capable-rabbit-19060.upstash.io:6379")
    if redis_url:
        return redis.Redis.from_url(redis_url, decode_responses=True)

    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


redis_client = _build_redis_client()


def _redis_available() -> bool:
    try:
        redis_client.ping()
        return True
    except Exception:
        return False


def get_conversation(conversation_id: str):
    data = None

    if _redis_available():
        data = redis_client.get(conversation_id)
    else:
        data = _memory_store.get(conversation_id)

    if not data:
        return None

    obj = json.loads(data)
    obj["phase"] = ScamPhase(obj["phase"])
    return obj


def save_conversation(conversation_id: str, state: dict):
    serializable = {
        "phase": state["phase"].value,
        "messages": state["messages"],
    }
    payload = json.dumps(serializable)

    if _redis_available():
        redis_client.set(conversation_id, payload)
    else:
        _memory_store[conversation_id] = payload


def add_flagged_intelligence(
    upi_ids: List[str] = None,
    bank_accounts: List[str] = None,
    phishing_links: List[str] = None
):
    """
    Add extracted intelligence to the flagged (blacklist) database.
    These will be instantly blocked in future conversations.
    """
    upi_ids = upi_ids or []
    bank_accounts = bank_accounts or []
    phishing_links = phishing_links or []
    
    if _redis_available():
        # Add to Redis sets
        if upi_ids:
            redis_client.sadd("flagged:upi_ids", *upi_ids)
            logger.info(f"🚩 Flagged {len(upi_ids)} UPI IDs: {upi_ids}")
        if bank_accounts:
            redis_client.sadd("flagged:bank_accounts", *bank_accounts)
            logger.info(f"🚩 Flagged {len(bank_accounts)} bank accounts: {bank_accounts}")
        if phishing_links:
            redis_client.sadd("flagged:phishing_links", *phishing_links)
            logger.info(f"🚩 Flagged {len(phishing_links)} phishing links: {phishing_links}")
    else:
        # Add to in-memory sets
        _flagged_upi_ids.update(upi_ids)
        _flagged_bank_accounts.update(bank_accounts)
        _flagged_phishing_links.update(phishing_links)
        logger.info(f"🚩 Flagged (in-memory): {len(upi_ids)} UPI, {len(bank_accounts)} accounts, {len(phishing_links)} links")


def check_flagged_intelligence(extracted_intelligence: Dict) -> tuple:
    """
    Check if any extracted intelligence matches flagged items.
    
    Returns: (is_flagged: bool, reason: str)
    """
    if not extracted_intelligence:
        return False, ""
    
    upi_ids = extracted_intelligence.get("upi_ids", [])
    bank_accounts = extracted_intelligence.get("bank_accounts", [])
    phishing_links = extracted_intelligence.get("phishing_links", [])
    
    if _redis_available():
        # Check Redis sets
        for upi in upi_ids:
            if redis_client.sismember("flagged:upi_ids", upi):
                logger.warning(f"🚨 FLAGGED UPI DETECTED: {upi}")
                return True, f"UPI ID {upi} has been flagged as suspicious in previous scams"
        
        for account in bank_accounts:
            if redis_client.sismember("flagged:bank_accounts", account):
                logger.warning(f"🚨 FLAGGED BANK ACCOUNT DETECTED: {account}")
                return True, f"Bank account {account} has been flagged as suspicious"
        
        for link in phishing_links:
            if redis_client.sismember("flagged:phishing_links", link):
                logger.warning(f"🚨 FLAGGED PHISHING LINK DETECTED: {link}")
                return True, f"Phishing link {link} has been reported multiple times"
    else:
        # Check in-memory sets
        for upi in upi_ids:
            if upi in _flagged_upi_ids:
                logger.warning(f"🚨 FLAGGED UPI DETECTED: {upi}")
                return True, f"UPI ID {upi} has been flagged as suspicious in previous scams"
        
        for account in bank_accounts:
            if account in _flagged_bank_accounts:
                logger.warning(f"🚨 FLAGGED BANK ACCOUNT DETECTED: {account}")
                return True, f"Bank account {account} has been flagged as suspicious"
        
        for link in phishing_links:
            if link in _flagged_phishing_links:
                logger.warning(f"🚨 FLAGGED PHISHING LINK DETECTED: {link}")
                return True, f"Phishing link {link} has been reported multiple times"
    
    return False, ""


def get_flagged_intelligence_stats() -> Dict:
    """Get statistics on flagged intelligence"""
    if _redis_available():
        upi_count = redis_client.scard("flagged:upi_ids")
        account_count = redis_client.scard("flagged:bank_accounts")
        link_count = redis_client.scard("flagged:phishing_links")
    else:
        upi_count = len(_flagged_upi_ids)
        account_count = len(_flagged_bank_accounts)
        link_count = len(_flagged_phishing_links)
    
    return {
        "flagged_upi_ids_count": upi_count,
        "flagged_bank_accounts_count": account_count,
        "flagged_phishing_links_count": link_count,
        "total_flagged": upi_count + account_count + link_count
    }
