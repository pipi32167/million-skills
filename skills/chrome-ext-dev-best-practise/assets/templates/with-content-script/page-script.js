// Page Script
// Injected into the main world of the page
// Can access page's JavaScript variables and functions

console.log('Page script injected');

// Communicate with content script via CustomEvent
function sendToExtension(data) {
  window.dispatchEvent(new CustomEvent('fromPage', {
    detail: data
  }));
}

// Listen for messages from extension
window.addEventListener('fromExtension', (event) => {
  console.log('Received from extension:', event.detail);
  
  // Handle extension message
  handleExtensionMessage(event.detail);
});

function handleExtensionMessage(message) {
  switch (message.action) {
    case 'GET_PAGE_DATA':
      // Access page's JavaScript variables
      const pageData = {
        // Access global variables from the page
        reactVersion: window.React?.version,
        vueVersion: window.Vue?.version,
        angularVersion: window.angular?.version
      };
      sendToExtension({ type: 'PAGE_DATA', data: pageData });
      break;
  }
}

// Example: Notify extension when page is ready
if (document.readyState === 'complete') {
  sendToExtension({ type: 'PAGE_READY' });
} else {
  window.addEventListener('load', () => {
    sendToExtension({ type: 'PAGE_READY' });
  });
}
