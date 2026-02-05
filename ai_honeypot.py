# ai_honeypot.py
from typing import List, Dict
from lifecycle import ScamPhase


def generate_honeypot_reply(
    history: List[Dict],
    scam_type: str,
    phase: ScamPhase
) -> str:
    """
    Generates a believable honeypot reply based on
    scam lifecycle phase and conversation context.

    This is rule-based now and can be replaced by AI later
    without changing the controller.
    """

    # Count scammer turns
    scammer_turns = len(
        [m for m in history if m["role"] == "scammer"]
    )

    last_message = history[-1]["content"].lower()

    # ---------------- INITIAL ----------------
    if phase == ScamPhase.INITIAL:
        return (
            "Sorry, I didn’t really understand that. "
            "What exactly do I need to do?"
        )

    # ---------------- ESCALATION ----------------
    if phase == ScamPhase.ESCALATION:
        if "upi" in last_message or "pay" in last_message:
            return (
                "I tried paying but it’s not going through. "
                "Can you send the details again?"
            )

        if "link" in last_message or "http" in last_message:
            return (
                "I’m not very comfortable clicking links. "
                "Is there another way to do this?"
            )

        return (
            "It’s a bit confusing on my side. "
            "Can you explain it once more?"
        )

    # ---------------- PAYMENT ----------------
    if phase == ScamPhase.PAYMENT:
        if scam_type == "upi_fraud":
            return (
                "UPI keeps failing for me. "
                "Is there a bank account I can transfer to instead?"
            )

        return (
            "The payment option isn’t working. "
            "What should I try next?"
        )

    # ---------------- MAX ESCALATION / EXIT ----------------
    if phase == ScamPhase.EXIT:
        if scammer_turns < 3:
            return (
                "It’s still not working. "
                "Can you send the official confirmation message?"
            )

        return (
            "I don’t want to make a mistake. "
            "Can you give me all the details clearly?"
        )

    # ---------------- FALLBACK ----------------
    return (
        "I’m trying to do this correctly. "
        "Please guide me step by step."
    )