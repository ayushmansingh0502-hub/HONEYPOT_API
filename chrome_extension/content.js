// Content script - Runs on Gmail pages to analyze emails
console.log("🛡️ Scam Shield content script loaded");

// Configuration
const CONFIG = {
  autoAnalyze: true,
  debounceMs: 1000,
  maxEmailLength: 5000
};

let debounceTimer = null;

/**
 * Extract email data from Gmail DOM
 */
function extractEmailData() {
  try {
    // Gmail HTML structure (may vary)
    const fromElement = document.querySelector('[data-email]');
    const fromEmail = fromElement?.getAttribute('data-email') || 
                      document.querySelector('[data-tooltip*="@"]')?.textContent || 
                      '';
    
    const fromName = document.querySelector('[email]')?.textContent || 
                     document.querySelector('[data-name]')?.textContent || 
                     '';
    
    const subject = document.querySelector('[data-subject]')?.textContent ||
                    document.title.split(' - ')[0] ||
                    '';
    
    const messageText = document.body.innerText;
    
    // Extract links
    const links = Array.from(document.querySelectorAll('a'))
      .map(a => a.href)
      .filter(href => href.startsWith('http'));
    
    return {
      from_email: fromEmail,
      from_name: fromName,
      subject: subject,
      message_text: messageText.substring(0, CONFIG.maxEmailLength),
      links: [...new Set(links)]
    };
  } catch (error) {
    console.error("❌ Error extracting email:", error);
    return null;
  }
}

/**
 * Send email for analysis
 */
async function analyzeCurrentEmail() {
  const emailData = extractEmailData();
  
  if (!emailData || !emailData.message_text) {
    console.log("⚠️ No email content found to analyze");
    return;
  }
  
  console.log("📧 Analyzing email:", emailData.from_email);
  
  // Send to background script
  chrome.runtime.sendMessage(
    {
      action: "analyzeEmail",
      data: emailData
    },
    (response) => {
      if (response.success) {
        showAnalysisResult(response.data, emailData);
      } else {
        showError(response.error);
      }
    }
  );
}

/**
 * Display analysis results on the page
 */
function showAnalysisResult(analysis, emailData) {
  console.log("📊 Displaying analysis:", analysis);
  
  // Create banner
  const banner = createAnalysisBanner(analysis);
  
  // Find Gmail's email container and inject banner
  const emailContainer = document.querySelector('[data-thread-id]');
  if (emailContainer) {
    const existingBanner = emailContainer.querySelector('.scam-shield-banner');
    if (existingBanner) existingBanner.remove();
    emailContainer.insertBefore(banner, emailContainer.firstChild);
  }
  
  // Highlight suspicious content
  if (analysis.is_scam && analysis.extracted_intelligence) {
    highlightSuspiciousContent(analysis.extracted_intelligence);
  }
}

/**
 * Create analysis banner element
 */
function createAnalysisBanner(analysis) {
  const banner = document.createElement('div');
  banner.className = 'scam-shield-banner';
  
  const riskLevel = analysis.risk?.risk_level || 'unknown';
  const riskScore = analysis.risk?.risk_score || 0;
  const bgColor = analysis.is_scam ? '#fee' : '#efe';
  const borderColor = analysis.is_scam ? '#c33' : '#3a3';
  const icon = analysis.is_scam ? '⚠️' : '✅';
  
  banner.innerHTML = `
    <div style="
      background: ${bgColor};
      border-left: 4px solid ${borderColor};
      padding: 12px 16px;
      margin: 8px 0;
      border-radius: 4px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 13px;
      line-height: 1.5;
    ">
      <div style="display: flex; gap: 8px; align-items: flex-start;">
        <span style="font-size: 18px; flex-shrink: 0;">${icon}</span>
        <div style="flex: 1;">
          <div style="font-weight: 600; color: ${analysis.is_scam ? '#c33' : '#3a3'}; margin-bottom: 4px;">
            ${analysis.is_scam ? 'Scam Alert' : 'Looks Safe'}
          </div>
          
          ${analysis.reasons && analysis.reasons.length > 0 ? `
            <div style="color: #555; font-size: 12px; margin-bottom: 4px;">
              ${analysis.reasons.join(' • ')}
            </div>
          ` : ''}
          
          <div style="color: #666; font-size: 12px;">
            Confidence: <strong>${(analysis.confidence * 100).toFixed(0)}%</strong> | 
            Risk: <strong>${riskScore}/100</strong>
          </div>
          
          ${analysis.extracted_intelligence?.upi_ids?.length > 0 ? `
            <div style="color: #c33; font-size: 12px; margin-top: 4px;">
              🚨 Found UPI IDs: ${analysis.extracted_intelligence.upi_ids.join(', ')}
            </div>
          ` : ''}
          
          ${analysis.extracted_intelligence?.phishing_links?.length > 0 ? `
            <div style="color: #c33; font-size: 12px; margin-top: 4px;">
              🔗 Found suspicious links: ${analysis.extracted_intelligence.phishing_links.slice(0, 2).join(', ')}
            </div>
          ` : ''}
        </div>
      </div>
    </div>
  `;
  
  return banner;
}

/**
 * Highlight suspicious UPIs, links, etc in email
 */
function highlightSuspiciousContent(intelligence) {
  // Highlight UPI IDs
  if (intelligence.upi_ids && intelligence.upi_ids.length > 0) {
    highlightText(intelligence.upi_ids, '#ffcccc', '#cc3333');
  }
  
  // Highlight phishing links
  if (intelligence.phishing_links && intelligence.phishing_links.length > 0) {
    const links = document.querySelectorAll('a');
    links.forEach(link => {
      if (intelligence.phishing_links.some(phish => link.href.includes(phish))) {
        link.style.backgroundColor = '#ffcccc';
        link.style.color = '#cc3333';
        link.style.fontWeight = 'bold';
        link.style.textDecoration = 'line-through';
      }
    });
  }
}

// Helper function to highlight text
function highlightText(texts, bgColor, textColor) {
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );
  
  let node;
  while (node = walker.nextNode()) {
    texts.forEach(text => {
      if (node.textContent.includes(text)) {
        const regex = new RegExp(`(${text})`, 'gi');
        const span = document.createElement('span');
        span.innerHTML = node.textContent.replace(regex, 
          `<span style="background: ${bgColor}; color: ${textColor}; font-weight: bold;">$1</span>`
        );
        node.parentNode.replaceChild(span, node);
      }
    });
  }
}

/**
 * Show error message
 */
function showError(errorMsg) {
  const banner = document.createElement('div');
  banner.className = 'scam-shield-error';
  banner.innerHTML = `
    <div style="
      background: #fef3cd;
      border-left: 4px solid #ffc107;
      padding: 12px 16px;
      margin: 8px 0;
      border-radius: 4px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 13px;
    ">
      ⚠️ Analysis unavailable: ${errorMsg}
    </div>
  `;
  
  const emailContainer = document.querySelector('[data-thread-id]');
  if (emailContainer) {
    emailContainer.insertBefore(banner, emailContainer.firstChild);
  }
}

/**
 * Debounced email analysis
 */
function debouncedAnalyze() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(analyzeCurrentEmail, CONFIG.debounceMs);
}

/**
 * Monitor Gmail for new emails
 */
function setupObservers() {
  // Watch for email thread changes
  const observer = new MutationObserver(() => {
    if (CONFIG.autoAnalyze) {
      debouncedAnalyze();
    }
  });
  
  // Observe the main content area for changes
  const mainContent = document.querySelector('[data-view-name="MAIN"]');
  if (mainContent) {
    observer.observe(mainContent, {
      childList: true,
      subtree: true,
      characterData: true
    });
    console.log("✅ Gmail observer attached");
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupObservers);
} else {
  setupObservers();
}

// Also analyze when user clicks on an email
document.addEventListener('click', (e) => {
  if (e.target.closest('[data-thread-id]') || e.target.closest('[role="main"]')) {
    debouncedAnalyze();
  }
}, true);

console.log("✅ Scam Shield content script initialized");
