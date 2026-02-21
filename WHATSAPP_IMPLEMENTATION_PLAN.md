# WhatsApp Honeypot Plugin - Implementation Plan

## 📱 Overview
Extend the honeypot system to detect and engage scammers directly via WhatsApp, capturing real conversations and training the AI model.

---

## 🎯 Phase 1: Architecture & Integration (Week 1)

### 1.1 WhatsApp Business API Setup
- [ ] Create WhatsApp Business Account (via Meta Business Suite)
- [ ] Get Phone Number ID and Access Token
- [ ] Set up Webhook URL for message receiving
- [ ] Configure allowed message types (text, images, documents)
- [ ] Register required templates for automated responses

**Resources Needed:**
- WhatsApp Business Account (free)
- Phone number for WhatsApp Business
- Webhook server (already have FastAPI backend)
- Meta Business Suite credentials

### 1.2 Backend Modifications
```
NEW FILE: whatsapp_integration.py
├── WhatsAppClient class
│   ├── send_message(phone_number, text)
│   ├── receive_message(webhook_payload)
│   ├── get_media(media_id)
│   └── mark_as_read(message_id)
├── WhatsAppSession management
│   ├── get_or_create_session(phone_number)
│   ├── track_user_state
│   └── handle_user_blocking
└── Media handling
    ├── download_images/videos
    ├── extract_text_from_images (OCR)
    └── store_evidence

NEW ENDPOINT: POST /whatsapp/webhook
├── Receives messages from WhatsApp
├── Validates signatures
├── Routes to conversation handler
└── Sends honeypot reply
```

**New Routes:**
```python
POST   /whatsapp/webhook                    # Receive messages
GET    /whatsapp/webhook                    # Webhook verification
POST   /whatsapp/send-message               # Send manual reply
GET    /whatsapp/conversations              # List conversations
GET    /whatsapp/conversation/{user_id}     # Get conversation history
POST   /whatsapp/media/analyze               # Analyze images/documents
DELETE /whatsapp/block-user                 # Block a scammer
```

---

## 🔧 Phase 2: Core Features (Week 2)

### 2.1 Message Receiving & Processing
```
Flow:
1. WhatsApp sends message to webhook
2. Validate webhook signature
3. Extract:
   - Phone number (sender)
   - Message text + timestamp
   - Media (images, documents)
   - Message type (text, image, document, audio)
4. Send to existing honeypot engine
5. Get AI response
6. Reply back to WhatsApp
```

### 2.2 Conversation Tracking
```python
# New database table: whatsapp_conversations
{
  id: UUID,
  phone_number: str (hashed for privacy),
  conversation_id: str (link to honeypot),
  start_time: datetime,
  message_count: int,
  last_message: datetime,
  status: "ACTIVE" | "BLOCKED" | "ARCHIVED",
  blocked_reason: str,
  scam_type: str,
  confidence: float,
  extracted_data: {
    upi_ids: [],
    bank_accounts: [],
    links: [],
    media_files: []
  }
}
```

### 2.3 Media Analysis
```python
# For images/documents sent by scammers
- Extract text from images (Tesseract/EasyOCR)
- Detect QR codes → extract URLs
- Identify proof of bank accounts, UPI IDs
- Screenshot analysis for phishing pages
- Document OCR for fake certificates/demands
```

---

## 📊 Phase 3: Intelligence & Analytics (Week 3)

### 3.1 Dashboard Endpoints
```
GET /whatsapp/stats
├── Total conversations tracked
├── Active scammers
├── Common scam types
├── Most used UPI IDs
├── Phishing domains found
└── Media evidence count

GET /whatsapp/recent-scammers
├── Last 10 active conversations
├── Scammer phone numbers (masked)
├── Conversation previews
└── Scam confidence scores

GET /whatsapp/evidence-library
├── All extracted UPI IDs
├── All bank accounts
├── All phishing links
├── Screenshot evidence
└── Document copies
```

### 3.2 Reporting & Export
```
- Export conversations as PDF
- Generate scammer profile report
- Statistics dashboard
- Export flagged intelligence to security services
```

---

## 🛡️ Phase 4: Safety & Compliance (Week 2-3)

### 4.1 User Privacy
- [ ] Hash phone numbers in database
- [ ] Encrypt sensitive data (UPI IDs, accounts)
- [ ] Comply with WhatsApp ToS
- [ ] Add user consent/disclaimer
- [ ] Auto-delete old conversations (90-day retention)

### 4.2 Safety Measures
- [ ] Block after X scam indicators detected
- [ ] Prevent accidental replies to real users
- [ ] Rate limiting per phone number
- [ ] Prevent honeypot number abuse
- [ ] Automated moderation for explicit content

### 4.3 Compliance
- [ ] WhatsApp Business API terms
- [ ] India cybercrime laws (IPC §420, etc.)
- [ ] GDPR data handling
- [ ] Evidence admissibility for legal proceedings

---

## 🏗️ Technical Implementation Details

### 4.1 WhatsApp Webhook Integration
```python
# main.py additions
from whatsapp_integration import WhatsAppClient

watsapp = WhatsAppClient(
    phone_number_id="YOUR_PHONE_ID",
    access_token="YOUR_ACCESS_TOKEN",
    webhook_verify_token="SECURE_TOKEN"
)

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Receive incoming messages from WhatsApp
    """
    signature = request.headers.get("x-hub-signature-256")
    
    # Verify webhook signature
    if not watsapp.verify_signature(await request.body(), signature):
        return {"error": "Invalid signature"}, 403
    
    payload = await request.json()
    
    for entry in payload["entry"]:
        for message in entry["changes"][0]["value"]["messages"]:
            phone = message["from"]
            text = message["text"]["body"]
            message_id = message["id"]
            
            # Process through honeypot
            response = await handle_message({
                "conversation_id": phone,
                "message": text
            })
            
            # Send honeypot reply back
            await whatsapp.send_message(
                phone,
                response["honeypot_reply"],
                reply_to=message_id
            )
            
            # Flag if scam + extracted data
            if response["analysis"]["is_scam"]:
                await storage.add_whatsapp_conversation(
                    phone_number=phone,
                    message_text=text,
                    response=response,
                    message_id=message_id
                )
    
    return {"status": "ok"}

@app.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(request: Request):
    """WhatsApp sends verification during setup"""
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if token == os.getenv("WHATSAPP_WEBHOOK_TOKEN"):
        return int(challenge)
    return {"error": "Invalid token"}, 403
```

### 4.2 Media Handling
```python
# whatsapp_integration.py
from PIL import Image
import pytesseract
import qrcode

class WhatsAppMediaHandler:
    async def analyze_image(self, media_id: str):
        """Extract text and QR codes from image"""
        image = await watsapp.download_media(media_id)
        
        # OCR text extraction
        text = pytesseract.image_to_string(image)
        
        # QR code detection
        qr_decoder = cv2.QRCodeDetector()
        data, _, _ = qr_decoder.detectAndDecode(image)
        
        return {
            "extracted_text": text,
            "qr_codes": [data] if data else [],
            "potential_upi": extract_upi_patterns(text),
            "potential_accounts": extract_account_patterns(text)
        }
```

### 4.3 Storage Extension
```python
# storage.py additions
async def add_whatsapp_conversation(
    phone_number: str,
    message_text: str,
    response: dict,
    message_id: str,
    media_data: dict = None
):
    """Store WhatsApp conversation"""
    key = f"whatsapp:conv:{hash_phone(phone_number)}"
    
    conversation = {
        "phone": hash_phone(phone_number),
        "messages": [{
            "id": message_id,
            "text": message_text,
            "timestamp": datetime.now().isoformat(),
            "is_scam": response["analysis"]["is_scam"],
            "confidence": response["analysis"]["confidence"],
            "reply": response["honeypot_reply"],
            "media": media_data
        }],
        "analysis": response["analysis"]
    }
    
    await redis_client.hset(key, "data", json.dumps(conversation))
    
    # Add to flagged list if scam
    if response["analysis"]["extracted_intelligence"]:
        await add_flagged_intelligence(
            response["analysis"]["extracted_intelligence"]
        )
```

---

## 📋 Required Dependencies

```python
# Add to requirements.txt
requests>=2.28.0              # WhatsApp API calls
httpx>=0.23.0                 # Async HTTP client
pillow>=9.0.0                 # Image processing
pytesseract>=0.3.10           # OCR
opencv-python>=4.6.0          # QR code detection
cryptography>=38.0.0          # Signature verification
phonenumbers>=8.12.0          # Phone number validation
pydantic-extra-types>=2.0.0   # Phone number types
```

---

## 🚀 Phase 5: Deployment (Week 4)

### 5.1 Setup Steps
```bash
1. Create WhatsApp Business Account
2. Get Phone Number ID and Access Token
3. Set webhook URL: https://your-railway-app.up.railway.app/whatsapp/webhook
4. Deploy updated backend to Railway
5. Configure Redis for WhatsApp conversations
6. Set environment variables:
   - WHATSAPP_PHONE_ID
   - WHATSAPP_ACCESS_TOKEN
   - WHATSAPP_WEBHOOK_TOKEN
   - WHATSAPP_BUSINESS_ACCOUNT_ID
7. Test with sample messages
```

### 5.2 Testing Checklist
- [ ] Send test message to WhatsApp number
- [ ] Verify message received by webhook
- [ ] Verify honeypot reply sent back
- [ ] Test media upload and OCR
- [ ] Test conversation history retrieval
- [ ] Test scammer blocking
- [ ] Verify Redis storage working
- [ ] Check rate limiting
- [ ] Test signature verification

---

## 📊 Admin Dashboard Features

```
/whatsapp/dashboard
├── Live active conversations (real-time)
├── Top scammers by frequency
├── Scam types breakdown (pie chart)
├── Geographic distribution (phone codes)
├── Most common UPI IDs
├── Evidence library (images/documents)
├── Conversation timeline
├── Media evidence gallery
└── Export/Report generation
```

---

## 🔒 Security Considerations

- [ ] WhatsApp signature validation (HMAC-SHA256)
- [ ] Phone number hashing (SHA-256 one-way)
- [ ] Rate limiting: 10 msgs/min per user, 100 msgs/min globally
- [ ] Auto-block after 15+ scam indicators
- [ ] Encrypt stored UPI IDs and bank accounts
- [ ] Audit logs for all admin actions
- [ ] Prevent DoS via webhook flooding
- [ ] Verify all media before processing

---

## 🎯 Success Metrics

After implementation, track:
- **Scammers caught**: Number of unique WhatsApp scammers identified
- **UPI IDs flagged**: How many unique UPI addresses extracted
- **Avg conversation length**: Messages before scam detected
- **Response time**: Latency of honeypot replies
- **Blocking accuracy**: False positive rate
- **Evidence quality**: Usable for law enforcement

---

## 📅 Timeline Summary

```
Week 1: WhatsApp API integration, webhook setup, message routing
Week 2: Conversation tracking, media handling, OCR
Week 3: Dashboard, analytics, reporting
Week 4: Testing, security hardening, deployment

Total: ~4 weeks for full production system
```

---

## 🚀 Quick Start Setup

```bash
# 1. Get WhatsApp Business Account
# Visit: https://www.whatsapp.com/business/

# 2. Get Meta API credentials from Business Dashboard

# 3. Update environment
echo "WHATSAPP_PHONE_ID=YOUR_ID" >> .env
echo "WHATSAPP_ACCESS_TOKEN=YOUR_TOKEN" >> .env
echo "WHATSAPP_WEBHOOK_TOKEN=YOUR_SECURE_TOKEN" >> .env

# 4. Deploy to Railway
git push

# 5. Configure webhook in Meta Business Suite
# URL: https://your-app.up.railway.app/whatsapp/webhook
# Verify Token: (your secure token from step 3)
```

---

## 💡 Future Enhancements

1. **Telegram integration** - Similar plugin for Telegram
2. **SMS honeypot** - Catch SMS-based scams
3. **Call monitoring** - Detect voice call scams
4. **AI improvement** - Learn from WhatsApp conversations
5. **Integration with law enforcement** - Direct reporting
6. **Multi-language support** - Hindi, Tamil, Bengali scams
7. **Deepfake detection** - Analyze profile pictures
8. **Social media scams** - Instagram, Facebook integration

---

**Ready to start? Which phase would you like to build first?**
