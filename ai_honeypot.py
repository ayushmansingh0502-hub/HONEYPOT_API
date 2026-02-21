# ai_honeypot.py - UPDATED WITH GOOGLE AI STUDIO
import google.generativeai as genai
import os
import logging
from typing import List, Dict
from lifecycle import ScamPhase

# Setup logging
logger = logging.getLogger("honeypot.ai")

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_AI_STUDIO_KEY", "AIzaSyDZSLIE_x0Zt74tgMWpXjuaz2yJGl-w5v4")

logger.info(f"🔑 API Key loaded: {'✅ YES' if API_KEY else '❌ NO'} (length: {len(API_KEY) if API_KEY else 0})")

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini model initialized successfully (gemini-1.5-flash)")
    except Exception as e:
        logger.error(f"❌ Model initialization failed: {e}")
        model = None
else:
    model = None
    logger.warning("⚠️ GOOGLE_AI_STUDIO_KEY not set. Using rule-based replies.")


def generate_honeypot_reply(
    history: List[Dict],
    scam_type: str,
    phase: ScamPhase
) -> str:
    """
    Generates a believable honeypot reply based on
    scam lifecycle phase and conversation context.

    NOW USES LLM (Google AI Studio/Gemini) when API key is available.
    Falls back to rule-based responses if API is unavailable.
    """

    # Try LLM generation first if API key is available
    if model and API_KEY:
        try:
            logger.info(f"🤖 Attempting LLM reply generation (phase: {phase.value})")
            reply = _generate_llm_reply(history, scam_type, phase)
            logger.info(f"✅ LLM reply generated: {reply[:50]}...")
            return reply
        except Exception as e:
            logger.error(f"❌ LLM reply generation FAILED: {type(e).__name__}: {str(e)}")
            # Fall through to rule-based responses
    else:
        logger.warning(f"⚠️ LLM not available (model={model is not None}, API_KEY={API_KEY is not None})")

    # Fallback: Original rule-based logic
    logger.info("🔄 Using rule-based fallback reply")
    return _generate_rule_based_reply(history, scam_type, phase)


def _generate_llm_reply(
    history: List[Dict],
    scam_type: str,
    phase: ScamPhase
) -> str:
    """
    Generate contextual reply using Google AI Studio (Gemini).
    """
    # Build conversation context (last 5 messages)
    context_lines = []
    for msg in history[-5:]:
        role = "Scammer" if msg["role"] == "scammer" else "You (Victim)"
        context_lines.append(f"{role}: {msg['content']}")
    context = "\n".join(context_lines)
    
    # Phase-specific guidance
    phase_guidance = {
        ScamPhase.INITIAL: "Show mild confusion. Ask what this is about in simple terms.",
        ScamPhase.PRESSURE: "Express worry but hesitation. Ask for clarification on the urgency.",
        ScamPhase.PAYMENT: "Seem willing to pay but claim technical difficulties. Ask for alternative payment methods.",
        ScamPhase.ESCALATION: "Show frustration with repeated failures. Request official confirmation or support number.",
        ScamPhase.EXIT: "Politely delay. Say you'll check with family/bank and get back to them."
    }
    
    # Scam type context
    scam_context = ""
    if scam_type == "upi_fraud":
        scam_context = "This is a UPI payment scam. Show confusion about payment apps and digital transactions."
    elif scam_type:
        scam_context = f"This is a {scam_type} scam. Act confused but willing to comply."
    
    prompt = f"""You are roleplaying as a CONFUSED VICTIM in a scam honeypot trap. Your goal is to keep the scammer engaged while sounding believable.

CURRENT SCAM PHASE: {phase.value}
YOUR STRATEGY: {phase_guidance.get(phase, 'Be confused and ask questions')}
{scam_context}

RECENT CONVERSATION:
{context}

Generate a realistic victim reply following these rules:
1. Maximum 2 short sentences (like a real WhatsApp/SMS message)
2. Use simple, everyday language (Indian English is fine)
3. Minor grammar mistakes are OK - sound human, not robotic
4. Show appropriate emotion for the phase (confusion, worry, frustration)
5. Keep the scammer engaged - ask clarifying questions
6. NO technical jargon or perfect grammar
7. Act like someone's grandmother or non-tech-savvy person

Examples of good replies:
- "I am not understanding what you are saying. Can you explain properly?"
- "The UPI is not working only. Is there any other way?"
- "Very urgent you are saying? But I am not able to do it. Please help."

YOUR REPLY:"""

    logger.debug(f"📤 Sending prompt to Gemini (length: {len(prompt)} chars)")
    
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.8,  # More creative for variety
            max_output_tokens=150
        )
    )
    
    logger.debug(f"📥 Received response from Gemini")
    
    reply = response.text.strip()
    
    # Remove quotes if LLM wrapped the reply
    if reply.startswith('"') and reply.endswith('"'):
        reply = reply[1:-1]
    if reply.startswith("'") and reply.endswith("'"):
        reply = reply[1:-1]
    
    return reply


def _generate_rule_based_reply(
    history: List[Dict],
    scam_type: str,
    phase: ScamPhase
) -> str:
    """
    Original rule-based reply generation (fallback).
    """
    # Count scammer turns
    scammer_turns = len(
        [m for m in history if m["role"] == "scammer"]
    )

    last_message = history[-1]["content"].lower()

    # ---------------- INITIAL ----------------
    if phase == ScamPhase.INITIAL:
        return (
            "Sorry, I didn't really understand that. "
            "What exactly do I need to do?"
        )

    # ---------------- ESCALATION ----------------
    if phase == ScamPhase.ESCALATION:
        if "upi" in last_message or "pay" in last_message:
            return (
                "I tried paying but it's not going through. "
                "Can you send the details again?"
            )

        if "link" in last_message or "http" in last_message:
            return (
                "I'm not very comfortable clicking links. "
                "Is there another way to do this?"
            )

        return (
            "It's a bit confusing on my side. "
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
            "The payment option isn't working. "
            "What should I try next?"
        )

    # ---------------- MAX ESCALATION / EXIT ----------------
    if phase == ScamPhase.EXIT:
        if scammer_turns < 3:
            return (
                "It's still not working. "
                "Can you send the official confirmation message?"
            )

        return (
            "I don't want to make a mistake. "
            "Can you give me all the details clearly?"
        )

    # ---------------- FALLBACK ----------------
    return (
        "I'm trying to do this correctly. "
        "Please guide me step by step."
    )
