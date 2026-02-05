from schemas import ScamAnalysisResponse
from intelligence import detect_scam, extract_intelligence
from storage import get_conversation, save_conversation
from lifecycle import ScamPhase
from phase_engine import next_phase
from honeypot_brain import honeypot_reply_for_phase
from scoring import compute_risk_score
from fingerprint import analyze_attacker

def handle_message(
    conversation_id: str,
    message: str,
    ip: str,
    user_agent: str
) -> ScamAnalysisResponse:
    # 1️⃣ Load or initialize conversation state
    state = get_conversation(conversation_id)

    if not state:
        state = {
            "phase": ScamPhase.INITIAL,
            "messages": []
        }

    current_phase: ScamPhase = state["phase"]
    history = state["messages"]

    # 2️⃣ Save scammer message
    history.append({
        "role": "scammer",
        "content": message
    })

    # 3️⃣ Detection + intelligence (history-aware)
    scammer_text = " ".join(
        m["content"] for m in history if m["role"] == "scammer"
    )
    detection = detect_scam(scammer_text)
    intelligence = None

    if detection.is_scam:
        intelligence = extract_intelligence(scammer_text)
        new_phase = next_phase(current_phase, message)
    else:
        new_phase = current_phase

    # 4️⃣ Generate honeypot reply (rule-based brain)
    reply = honeypot_reply_for_phase(new_phase)

    # 🔍 Build attacker fingerprint
    fingerprint = analyze_attacker(
        history=history,
        ip=ip,
        user_agent=user_agent
    )

    # 📊 Risk scoring
    risk = compute_risk_score(
        detection=detection,
        fingerprint=fingerprint,
        phase=new_phase,
        intelligence=intelligence
    )

    # 5️⃣ Save honeypot reply
    history.append({
        "role": "honeypot",
        "content": reply
    })

    # 6️⃣ Persist updated conversation
    save_conversation(
        conversation_id,
        {
            "phase": new_phase,
            "messages": history
        }
    )

    # 7️⃣ Return API response
    return ScamAnalysisResponse(
        is_scam=detection.is_scam,
        scam_type="upi_fraud" if detection.is_scam else None,
        extracted_intelligence=intelligence,
        confidence=detection.confidence,
        honeypot_reply=reply,
        risk=risk
    )