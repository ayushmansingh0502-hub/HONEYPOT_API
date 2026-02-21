// Background Service Worker - Handles API calls and message routing
const API_BASE = "https://web-production-b7ac.up.railway.app";
const API_KEY = "hackathon-secret-key";

// Store API key securely in extension storage
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    apiKey: API_KEY,
    apiBase: API_BASE,
    autoAnalyze: true,
    highlightScams: true
  });
  console.log("🛡️ Scam Shield initialized");
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeEmail") {
    analyzeEmail(request.data)
      .then(result => {
        console.log("✅ Analysis result:", result);
        sendResponse({ success: true, data: result });
      })
      .catch(error => {
        console.error("❌ Analysis error:", error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Will respond asynchronously
  }
  
  if (request.action === "getFlaggedStats") {
    getFlaggedStats()
      .then(stats => {
        sendResponse({ success: true, data: stats });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
});

/**
 * Analyze email using backend API
 */
async function analyzeEmail(emailData) {
  const { from_email, from_name, subject, message_text, links } = emailData;
  
  const payload = {
    from_email: from_email || "unknown@example.com",
    from_name: from_name || "Unknown",
    subject: subject || "",
    message_text: message_text || "",
    links: links || []
  };
  
  console.log("📤 Sending to API:", payload);
  
  const response = await fetch(`${API_BASE}/analyze-email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY
    },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  const result = await response.json();
  console.log("✅ API Response:", result);
  return result;
}

/**
 * Get flagged intelligence statistics
 */
async function getFlaggedStats() {
  const response = await fetch(`${API_BASE}/admin/flagged-intelligence`, {
    method: "GET",
    headers: {
      "x-api-key": API_KEY
    }
  });
  
  if (!response.ok) {
    throw new Error(`Stats API error: ${response.status}`);
  }
  
  return await response.json();
}

// Log service worker is active
console.log("🔒 Scam Shield background worker loaded");
