// Content Script
// Runs in the context of web pages

console.log('Content script loaded');

// Listen for messages from background/popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case 'EXTRACT_DATA':
          const data = extractPageData();
          sendResponse({ success: true, data });
          break;
        case 'HIGHLIGHT':
          highlightElements(message.selector);
          sendResponse({ success: true });
          break;
        case 'GET_SELECTION':
          const selection = window.getSelection().toString();
          sendResponse({ success: true, data: selection });
          break;
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Content script error:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();
  return true; // Keep channel open for async
});

// Extract data from the page
function extractPageData() {
  return {
    title: document.title,
    url: location.href,
    headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
      level: h.tagName,
      text: h.textContent.trim()
    })),
    links: Array.from(document.querySelectorAll('a[href]')).map(a => ({
      text: a.textContent.trim(),
      href: a.href
    })).slice(0, 10)
  };
}

// Highlight elements on the page
function highlightElements(selector) {
  // Remove existing highlights
  document.querySelectorAll('.ext-highlight').forEach(el => {
    el.classList.remove('ext-highlight');
  });
  
  // Add new highlights
  const elements = document.querySelectorAll(selector);
  elements.forEach(el => {
    el.classList.add('ext-highlight');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  
  // Inject highlight styles if not present
  if (!document.getElementById('ext-highlight-styles')) {
    const style = document.createElement('style');
    style.id = 'ext-highlight-styles';
    style.textContent = `
      .ext-highlight {
        outline: 3px solid #1a73e8 !important;
        outline-offset: 2px !important;
        background: rgba(26, 115, 232, 0.1) !important;
      }
    `;
    document.head.appendChild(style);
  }
  
  return elements.length;
}

// Observe DOM changes
const observer = new MutationObserver((mutations) => {
  // Handle DOM changes
  for (const mutation of mutations) {
    if (mutation.type === 'childList') {
      // New elements added
      mutation.addedNodes.forEach(node => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Process new element
        }
      });
    }
  }
});

// Start observing
observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  observer.disconnect();
});

// Optional: Inject script into page's main world
function injectPageScript() {
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('page-script.js');
  script.onload = () => script.remove();
  (document.head || document.documentElement).appendChild(script);
}

// Listen for messages from page script
window.addEventListener('message', (event) => {
  // Verify origin if needed
  if (event.source !== window) return;
  
  if (event.data.type && event.data.type === 'FROM_PAGE') {
    console.log('Received from page:', event.data.payload);
    // Handle page message
  }
});
