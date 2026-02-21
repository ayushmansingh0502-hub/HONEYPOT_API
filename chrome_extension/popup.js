// Popup script - Handle popup UI events
console.log("📋 Popup initialized");

// Load settings on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadFlaggedStats();
  loadSettings();
  setupToggleButtons();
});

/**
 * Load and display flagged intelligence stats
 */
function loadFlaggedStats() {
  chrome.runtime.sendMessage(
    { action: "getFlaggedStats" },
    (response) => {
      if (response.success) {
        const stats = response.data;
        document.getElementById('stat-upi').textContent = stats.flagged_upi_ids_count || 0;
        document.getElementById('stat-accounts').textContent = stats.flagged_bank_accounts_count || 0;
        document.getElementById('stat-links').textContent = stats.flagged_phishing_links_count || 0;
        document.getElementById('stat-total').textContent = stats.total_flagged || 0;
      } else {
        console.error("Failed to load stats:", response.error);
        // Show error but don't break the UI
        document.getElementById('stat-total').textContent = "Error";
      }
    }
  );
}

/**
 * Load settings from storage
 */
function loadSettings() {
  chrome.storage.sync.get(['autoAnalyze', 'highlightScams'], (items) => {
    const autoAnalyze = items.autoAnalyze !== false; // default true
    const highlight = items.highlightScams !== false; // default true
    
    setToggleState('toggle-auto-analyze', autoAnalyze);
    setToggleState('toggle-highlight', highlight);
  });
}

/**
 * Setup toggle button event listeners
 */
function setupToggleButtons() {
  const autoAnalyzeToggle = document.getElementById('toggle-auto-analyze');
  const highlightToggle = document.getElementById('toggle-highlight');
  
  autoAnalyzeToggle.addEventListener('click', () => {
    const isActive = autoAnalyzeToggle.classList.toggle('active');
    chrome.storage.sync.set({ autoAnalyze: isActive });
  });
  
  highlightToggle.addEventListener('click', () => {
    const isActive = highlightToggle.classList.toggle('active');
    chrome.storage.sync.set({ highlightScams: isActive });
  });
}

/**
 * Helper: Set toggle button state
 */
function setToggleState(elementId, isActive) {
  const element = document.getElementById(elementId);
  if (isActive) {
    element.classList.add('active');
  } else {
    element.classList.remove('active');
  }
}

// Auto-refresh stats every 30 seconds
setInterval(loadFlaggedStats, 30000);
