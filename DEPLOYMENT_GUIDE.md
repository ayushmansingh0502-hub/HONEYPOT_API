# 📖 Complete Deployment Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Getting API Keys](#getting-api-keys)
3. [Local Setup](#local-setup)
4. [Testing](#testing)
5. [Deployment to Render](#deployment-to-render)
6. [Monitoring & Logs](#monitoring--logs)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

## Architecture Overview

Your honeypot uses an intelligent multi-layered approach:

```
Incoming Message
    ↓
Intelligence Module (LLM-powered scam detection)
    ↓
Conversation State Manager (Redis)
    ↓
Lifecycle Engine (tracks scam phases)
    ↓
AI Reply Generator (contextual LLM responses)
    ↓
Risk Scoring & Fingerprinting
    ↓
Response sent back to scammer
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| `intelligence.py` | Detects scams | Google AI Studio (Gemini) |
| `ai_honeypot.py` | Generates replies | Google AI Studio (Gemini) |
| `controller.py` | Orchestrates logic | Python business logic |
| `storage.py` | Persists conversations | Redis |
| `phase_engine.py` | Tracks scam progression | State machine |
| `scoring.py` | Calculates risk | Risk algorithm |

---

## Getting API Keys

### 1. Google AI Studio Key (FREE - No Credit Card)

**Why?** Powers scam detection and contextual replies

**Steps:**
1. Open https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click blue "Create API Key" button
4. Select your project (or create new)
5. Copy the key from popup (starts with `AIza...`)

**Limits:**
- 250 free requests per day
- Perfect for ~100-150 conversations/day
- Resets at midnight UTC

**Save it:** You'll need this in Step 3

### 2. Upstash Redis (FREE - No Credit Card)

**Why?** Stores conversation history for state tracking

**Steps:**
1. Go to https://console.upstash.com
2. Click "Sign Up" (use GitHub login - easiest)
3. Accept defaults, verify email
4. Click "Create Database"
5. Choose:
   - **Type:** Redis
   - **Region:** Pick closest to you (e.g., us-east-1)
   - **Eviction Policy:** Noevict (keep data)
6. Wait 30 seconds for creation
7. Click on your database
8. Copy "Redis URL" from details (format: `redis://...`)

**Limits:**
- 10,000 commands/day free
- ~500-1000 commands per day (you'll use ~5 per message)
- Perfect for this use case

**Save it:** You'll need this in Step 3

---

## Local Setup

### Prerequisites
- Python 3.8+ (`python --version`)
- pip installed
- Git installed

### Installation

```bash
# 1. Clone/enter your project
cd /path/to/HONEY_POT

# 2. Create virtual environment (optional but recommended)
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Edit .env with your keys
# Open .env in your editor and replace:
# GOOGLE_AI_STUDIO_KEY=AIza... (paste your Google key)
# REDIS_URL=redis://... (paste your Upstash Redis URL)
```

### Verify Installation

```bash
# Check Python packages
pip list | grep -E "fastapi|google-generativeai|redis"

# Should show:
# fastapi          0.115.5
# google-generativeai 0.8.3
# redis            5.0.8
```

---

## Testing

### Run Local Tests

```bash
# Make sure .env is set up with real API keys
python test_local.py
```

**Expected output:**
```
🧪 Testing Honeypot...
✅ Module imports OK
✅ Environment variables loaded
✅ Google AI Studio API responsive
✅ Redis connection OK
✅ Scam detection working
✅ Reply generation working
✅ All tests passed!
```

### Manual Testing

```bash
# Start local server
uvicorn main:app --reload

# In another terminal, send test messages
curl -X POST http://localhost:8000/honeypot \
  -H "x-api-key: hackathon-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test-001",
    "message": "Your account is blocked. Pay ₹500 now!"
  }'

# Expected response:
# {
#   "conversation_id": "test-001",
#   "is_scam": true,
#   "confidence": 0.95,
#   "reply": "I am not understanding this. Why is my account blocked? What should I do?"
# }
```

---

## Deployment to Render

### Option A: Deploy via Render Dashboard (Recommended)

#### 1. Push to GitHub

```bash
git add .
git commit -m "Add honeypot deployment setup"
git push origin main
```

#### 2. Create Render Service

1. Go to https://render.com
2. Sign up/login
3. Click "New +" → "Web Service"
4. Click "Connect Account" → select your GitHub repo
5. Choose your repo from the list
6. Fill in service details:
   - **Name:** `honeypot-api`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Region:** Pick closest (e.g., US-East)

#### 3. Add Environment Variables

Click "Environment" section:
```
GOOGLE_AI_STUDIO_KEY = AIza...your-key...
REDIS_URL = redis://default:password@host.upstash.io:port
API_KEY = hackathon-secret-key
```

#### 4. Deploy

Click "Create Web Service"

**Wait 3-5 minutes for build to complete**

You'll see:
```
=== Build successful! ===
=== Deploying v1 ===
=== Deployment successful! ===
```

Your app URL: `https://honeypot-api.onrender.com`

### Option B: Deploy via GitHub Actions (Advanced)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: |
          curl https://api.render.com/deploy/srv-xxx?key=${{ secrets.RENDER_DEPLOY_KEY }}
```

---

## Testing Production Deployment

### 1. Get Your Live URL

From Render dashboard, copy your service URL (e.g., `https://honeypot-api.onrender.com`)

### 2. Test Endpoint

```bash
# Replace with your actual URL
curl -X POST https://honeypot-api.onrender.com/honeypot \
  -H "x-api-key: hackathon-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "prod-test-001",
    "message": "Pay ₹500 now or your account will be blocked!"
  }'
```

**Expected response (within 2 seconds):**
```json
{
  "conversation_id": "prod-test-001",
  "is_scam": true,
  "confidence": 0.95,
  "reply": "I am confused. Why are you asking for money? This seems strange."
}
```

### 3. Multi-Turn Conversation Test

```bash
# Message 1
curl -X POST https://honeypot-api.onrender.com/honeypot \
  -H "x-api-key: hackathon-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "conv-001", "message": "Your account verification failed"}'

# Message 2 - Notice how reply should be different and contextual
curl -X POST https://honeypot-api.onrender.com/honeypot \
  -H "x-api-key: hackathon-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "conv-001", "message": "Send ₹999 within 1 hour"}'

# Message 3
curl -X POST https://honeypot-api.onrender.com/honeypot \
  -H "x-api-key: hackathon-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "conv-001", "message": "Why are you not cooperating?"}'
```

Each reply should be different and contextual to the conversation phase.

---

## Monitoring & Logs

### View Live Logs (Render)

1. Go to your service in Render dashboard
2. Click "Logs" tab
3. See real-time logs as messages come in

**Watch for:**
- ✅ API key loaded successfully
- ✅ Redis connection working
- ❌ Errors (will show here)
- ✅ Response times

### Key Log Messages

```
[2024-02-20] INFO: Service starting...
[2024-02-20] INFO: GOOGLE_AI_STUDIO_KEY configured
[2024-02-20] INFO: Redis connected to upstash.io
[2024-02-20] INFO: POST /honeypot from 1.2.3.4
[2024-02-20] INFO: Scam detected, confidence: 0.95
[2024-02-20] INFO: Reply generated in 0.8s
```

### Metrics to Monitor

| Metric | Target | How to Check |
|--------|--------|-----------|
| Response Time | <2s | Render Logs |
| Detection Accuracy | >0.8 confidence | Test messages |
| Uptime | >99% | Render Dashboard |
| Error Rate | <1% | Logs tab |

---

## Troubleshooting

### Problem: "Module 'google.generativeai' not found"

**Cause:** Dependencies not installed

**Fix:**
```bash
# Local: reinstall
pip install -r requirements.txt

# Render: Check build command
# Should be: pip install -r requirements.txt
# In Render dashboard: Settings → Build Command
```

### Problem: "GOOGLE_AI_STUDIO_KEY not set"

**Cause:** Environment variable missing

**Fix:**
1. Render Dashboard → Your Service
2. Settings → Environment
3. Check if variable exists
4. If not, add: `GOOGLE_AI_STUDIO_KEY = AIza...`
5. Redeploy service

### Problem: "Redis connection refused"

**Cause:** Wrong Redis URL

**Fix:**
1. Get correct URL from https://console.upstash.com
2. Format should be: `redis://default:PASSWORD@HOST:PORT`
3. Update in Render Environment
4. Redeploy

### Problem: Slow responses (>5 seconds)

**Cause:** Long API latency or quota limits

**Fix:**
- Check Google AI Studio quota: https://aistudio.google.com/app/apikeys
- If near limits (250 requests/day), upgrade API plan
- Check Render logs for timeout messages

### Problem: "Invalid API Key"

**Cause:** 
- API key wrong
- API key expired
- API key from wrong project

**Fix:**
1. Go to https://aistudio.google.com/apikey
2. Verify key starts with `AIza...`
3. Create new key if needed
4. Update in Render Environment
5. Redeploy

### Problem: Replies are same/robotic

**Cause:** LLM not responding, using fallback

**Fix:**
1. Check Render logs for LLM errors
2. Verify GOOGLE_AI_STUDIO_KEY is set
3. Check if you hit daily quota (250 requests)
4. Try again after quota resets (midnight UTC)

### Quota Exceeded

**Symptoms:**
- Getting same reply every time
- Logs show "429 Too Many Requests"

**Fix:**
- Free tier is 250 requests/day = limited use
- Each conversation uses 2-3 requests
- Can handle ~100 conversations/day
- Wait until next day for quota reset
- Or upgrade API plan if heavy usage

---

## Next Steps

### 1. Basic Monitoring
```bash
# Set up simple monitoring script
while true; do
  curl -s https://your-app.onrender.com/health || echo "DOWN"
  sleep 300
done
```

### 2. Add Analytics
Track which scam types are detected:

```python
# In controller.py
def log_analytics(scam_type, confidence, reply_time):
    analytics.log({
        "type": scam_type,
        "confidence": confidence,
        "reply_time": reply_time,
        "timestamp": datetime.now()
    })
```

### 3. Rate Limiting
Protect your free quota:

```python
# In main.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/honeypot")
@limiter.limit("20/minute")
async def honeypot(request: Request):
    # Your endpoint
```

### 4. Webhooks
Send alerts when high-risk scams detected:

```python
if confidence > 0.9:
    webhook.send_alert({
        "message": message,
        "confidence": confidence,
        "type": scam_type
    })
```

### 5. Multi-Language Support
Extend to Hindi, Tamil, etc.:

```python
# In intelligence.py
def detect_scam_multilingual(message, language="auto"):
    # Translate to English first, then detect
    translated = translate(message, language, "en")
    return detect_scam(translated)
```

---

## Checklist Before Going Live

- [ ] Google AI Studio key obtained and tested
- [ ] Upstash Redis database created and connected
- [ ] Code pushed to GitHub
- [ ] Deployed to Render with no build errors
- [ ] Environment variables set correctly in Render
- [ ] Local test passed (`python test_local.py`)
- [ ] Production test passed (curl to live endpoint)
- [ ] No errors in Render logs
- [ ] Responses are contextual (not robotic)
- [ ] Conversation history being stored

---

## Support

**Documentation:**
- See QUICKSTART.md for 5-minute deploy
- See CHANGES.md for what's new
- See main.py for API schema

**Common fixes:**
1. Check Render logs
2. Verify environment variables
3. Re-run local tests
4. Check API key validity

**Still stuck?**
Check that:
- .env file exists locally with real keys
- Render environment variables match .env
- redis:// URL has correct format
- API key starts with AIza...

---

Happy hunting! 🍯
