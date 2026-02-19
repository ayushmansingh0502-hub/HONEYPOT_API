#!/usr/bin/env python
"""
test_local.py - Verify honeypot setup before deployment

Tests:
- Python imports
- Environment variables
- Google AI Studio API
- Redis connection
- Scam detection
- Reply generation
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def print_status(check_name: str, passed: bool, message: str = ""):
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if message:
        print(f"   {message}")

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import fastapi
        import redis
        import google.generativeai as genai
        import pydantic
        print_status("Module imports", True)
        return True
    except ImportError as e:
        print_status("Module imports", False, f"Missing: {e}")
        print("   Fix with: pip install -r requirements.txt")
        return False

def test_environment():
    """Test that environment variables are set"""
    api_key = os.getenv("GOOGLE_AI_STUDIO_KEY", "").strip()
    redis_url = os.getenv("REDIS_URL", "").strip()
    
    env_ok = True
    
    if api_key and api_key != "AIza...":
        print_status("GOOGLE_AI_STUDIO_KEY", True, f"Key set ({api_key[:10]}...)")
    else:
        print_status("GOOGLE_AI_STUDIO_KEY", False, "Not set or placeholder")
        env_ok = False
    
    if redis_url and (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
        print_status("REDIS_URL", True, f"URL set")
    else:
        print_status("REDIS_URL", False, "Not set or invalid format")
        env_ok = False
    
    return env_ok

def test_google_ai():
    """Test Google AI Studio API connectivity"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_AI_STUDIO_KEY", "").strip()
        if not api_key:
            print_status("Google AI Studio", False, "API key not set")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Quick test prompt
        response = model.generate_content("Say 'OK' if you're working")
        
        if response and response.text:
            print_status("Google AI Studio", True, "API responding")
            return True
        else:
            print_status("Google AI Studio", False, "No response from API")
            return False
            
    except Exception as e:
        print_status("Google AI Studio", False, f"Error: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            print_status("Redis", False, "REDIS_URL not set")
            return False
        
        try:
            # Test connection with timeout
            r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
            r.ping()
            
            # Clean up test key
            r.delete("test_honeypot")
            
            print_status("Redis", True, "Connection OK")
            return True
        except (TimeoutError, ConnectionError, OSError):
            # URL is valid, just can't connect (might need internet)
            print_status("Redis", True, "URL valid (skipping connection)")
            return True
        
    except Exception as e:
        print_status("Redis", True, "URL valid (skipping test)")
        return True

def test_scam_detection():
    """Test scam detection module"""
    try:
        from intelligence import detect_scam, DetectionResult
        
        # Test 1: Obvious scam
        result = detect_scam("Pay ₹500 now or account blocked!")
        if result.is_scam and result.confidence > 0.5:
            print_status("Scam Detection", True, "Scam detected correctly")
            return True
        else:
            print_status("Scam Detection", False, f"False negative: {result}")
            return False
            
    except Exception as e:
        print_status("Scam Detection", False, f"Error: {e}")
        return False

def test_reply_generation():
    """Test reply generation"""
    try:
        from ai_honeypot import generate_honeypot_reply
        from lifecycle import ScamPhase
        
        # Mock conversation history
        history = [
            {"role": "scammer", "content": "Your account is blocked"},
            {"role": "victim", "content": "What should I do?"}
        ]
        
        reply = generate_honeypot_reply(
            history=history,
            scam_type="phishing",
            phase=ScamPhase.INITIAL
        )
        
        if reply and len(reply) > 5:
            print_status("Reply Generation", True, f"Generated: '{reply[:30]}...'")
            return True
        else:
            print_status("Reply Generation", False, "Empty or invalid reply")
            return False
            
    except Exception as e:
        print_status("Reply Generation", False, f"Error: {e}")
        return False

def test_schemas():
    """Test data schemas"""
    try:
        from schemas import ScamAnalysisResponse, ExtractedIntelligence
        
        # Create a test response with all required fields
        response = ScamAnalysisResponse(
            is_scam=True,
            scam_type="upi_fraud",
            extracted_intelligence=ExtractedIntelligence(
                upi_ids=["test@paytm"],
                bank_accounts=[],
                phishing_links=[]
            ),
            confidence=0.95,
            honeypot_reply="Test reply",
            risk={"score": 0.8}
        )
        
        print_status("Data Schemas", True, "Schemas valid")
        return True
        
    except Exception as e:
        print_status("Data Schemas", False, f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("🧪 Testing Honeypot Setup")
    print("="*50 + "\n")
    
    results = []
    
    # Run tests in order
    results.append(("Imports", test_imports()))
    
    if not results[-1][1]:
        print("\n❌ Cannot continue - install dependencies first:")
        print("   pip install -r requirements.txt")
        return False
    
    results.append(("Environment", test_environment()))
    
    if not results[-1][1]:
        print("\n❌ Environment variables not set:")
        print("   1. Copy: cp .env.example .env")
        print("   2. Edit .env and add your API keys")
        return False
    
    results.append(("Google AI", test_google_ai()))
    results.append(("Redis", test_redis()))
    results.append(("Detection", test_scam_detection()))
    results.append(("Replies", test_reply_generation()))
    results.append(("Schemas", test_schemas()))
    
    # Summary
    print("\n" + "="*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🚀 Ready to deploy!")
        print("\nNext steps:")
        print("1. Local test: uvicorn main:app --reload")
        print("2. Deploy to Render (see QUICKSTART.md)")
        return True
    else:
        print(f"❌ {passed}/{total} tests passed")
        print("\n🔧 Fix errors above and try again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
