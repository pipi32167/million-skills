// Background Service Worker
// Handles events and coordinates between popup and content scripts

console.log('Service Worker initialized');

// Handle extension icon click
chrome.action.onClicked.addListener(async (tab) => {
  // Inject and execute content script
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // This runs in the content script context
        return {
          title: document.title,
          url: location.href
        };
      }
    });
    
    console.log('Page data:', results[0].result);
  } catch (error) {
    console.error('Script injection failed:', error);
  }
});

// Handle messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case 'INJECT_SCRIPT':
          const result = await injectScript(sender.tab.id, message.file);
          sendResponse({ success: true, result });
          break;
        case 'GET_TAB_DATA':
          const data = await getTabData(sender.tab?.id);
          sendResponse({ success: true, data });
          break;
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Error:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();
  return true;
});

// Inject script into a tab
async function injectScript(tabId, file) {
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    files: [file]
  });
  return results;
}

// Get data from a tab's content script
async function getTabData(tabId) {
  if (!tabId) return null;
  
  try {
    return await chrome.tabs.sendMessage(tabId, {
      action: 'EXTRACT_DATA'
    });
  } catch (error) {
    // Content script not loaded
    console.log('Content script not loaded in tab:', tabId);
    return null;
  }
}

// Handle tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    console.log('Tab updated:', tab.url);
    // Perform actions when page loads
  }
});

// Periodic cleanup task
chrome.alarms.create('cleanup', { periodInMinutes: 30 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'cleanup') {
    performCleanup();
  }
});

async function performCleanup() {
  // Clean up old data
  const data = await chrome.storage.local.get(null);
  const now = Date.now();
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours
  
  for (const [key, value] of Object.entries(data)) {
    if (value.timestamp && now - value.timestamp > maxAge) {
      await chrome.storage.local.remove(key);
    }
  }
}
