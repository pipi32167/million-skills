// Background Service Worker
// Runs in extension context, handles events and API calls

console.log('Service Worker initialized');

// Handle extension icon click
chrome.action.onClicked.addListener(async (tab) => {
  console.log('Extension clicked on tab:', tab.id);
});

// Handle messages from popup/content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case 'GET_DATA':
          const data = await getData();
          sendResponse({ success: true, data });
          break;
        case 'SET_DATA':
          await setData(message.payload);
          sendResponse({ success: true });
          break;
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Message handling error:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();
  return true; // Keep channel open for async
});

// Use alarms instead of setInterval
chrome.alarms.create('refresh', { periodInMinutes: 5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'refresh') {
    performPeriodicTask();
  }
});

async function getData() {
  const result = await chrome.storage.local.get('data');
  return result.data || {};
}

async function setData(data) {
  await chrome.storage.local.set({ data });
}

async function performPeriodicTask() {
  console.log('Performing periodic task');
  // Your periodic logic here
}
