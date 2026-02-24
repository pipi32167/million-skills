# Messaging Reference

## Table of Contents

- [One-time Messages](#one-time-messages)
- [Long-lived Connections](#long-lived-connections)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)

## One-time Messages

Use for simple request-response patterns.

### Basic Pattern

```javascript
// Sender
const response = await chrome.runtime.sendMessage({
  action: 'getData',
  payload: { id: 123 }
});

// Receiver
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getData') {
    processData(message.payload).then(data => {
      sendResponse({ success: true, data });
    });
    return true; // Keep channel open for async
  }
});
```

### Async/Await Pattern

```javascript
// Modern approach (Chrome 146+)
chrome.runtime.onMessage.addListener(async (message, sender) => {
  if (message.action === 'fetch') {
    const response = await fetch(message.url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }
});
```

### From Content Script to Background

```javascript
// content.js
const result = await chrome.runtime.sendMessage({
  type: 'EXTRACT_DATA',
  selector: '.article'
});
```

```javascript
// background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'EXTRACT_DATA') {
    // sender.tab contains tab info
    console.log('From tab:', sender.tab.id);
    
    processExtraction(message.selector).then(data => {
      sendResponse({ data });
    });
    return true;
  }
});
```

### From Background to Content Script

```javascript
// background.js
const tabs = await chrome.tabs.query({ url: '*://example.com/*' });
for (const tab of tabs) {
  try {
    await chrome.tabs.sendMessage(tab.id, {
      type: 'REFRESH_UI'
    });
  } catch (e) {
    // Content script not loaded in this tab
  }
}
```

## Long-lived Connections

Use for multiple messages or streaming data.

### Basic Connection

```javascript
// Create connection
const port = chrome.runtime.connect({ name: 'data-stream' });

port.postMessage({ type: 'subscribe', topic: 'updates' });

port.onMessage.addListener((msg) => {
  console.log('Received:', msg);
});

port.onDisconnect.addListener(() => {
  console.log('Disconnected');
});
```

```javascript
// Handle connections
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'data-stream') {
    const subscription = createSubscription((data) => {
      port.postMessage(data);
    });
    
    port.onDisconnect.addListener(() => {
      subscription.unsubscribe();
    });
  }
});
```

### Port Communication to Content Script

```javascript
// From popup to content script
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
const port = chrome.tabs.connect(tab.id, { name: 'page-control' });

port.postMessage({ action: 'scrollTo', position: 1000 });
```

## Error Handling

### Timeout Pattern

```javascript
async function sendMessageWithTimeout(message, timeout = 5000) {
  return Promise.race([
    chrome.runtime.sendMessage(message),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Message timeout')), timeout)
    )
  ]);
}
```

### Try-Catch Pattern

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      const result = await handleMessage(message);
      sendResponse({ success: true, data: result });
    } catch (error) {
      console.error('Message handling error:', error);
      sendResponse({ 
        success: false, 
        error: error.message,
        code: error.code 
      });
    }
  })();
  return true;
});
```

### Serialization Errors

```javascript
// ❌ Functions cannot be serialized
sendResponse({ callback: () => {} });

// ✅ Only JSON-serializable data
sendResponse({ data: 'string', count: 123, flag: true });

// ❌ Circular references
const obj = {}; obj.self = obj;
sendResponse(obj);

// ✅ Use structuredClone or JSON.stringify
sendResponse(JSON.parse(JSON.stringify(data)));
```

## Security Considerations

### Validate Message Origin

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Validate sender
  if (!sender.id || sender.id !== chrome.runtime.id) {
    console.warn('Invalid sender:', sender.id);
    return;
  }
  
  // Validate message format
  if (!message || typeof message !== 'object') {
    return;
  }
  
  // Validate action type
  const validActions = ['GET_DATA', 'SET_DATA', 'DELETE'];
  if (!validActions.includes(message.action)) {
    return;
  }
  
  // Process message
});
```

### Content Script Validation

Content scripts are less trustworthy - assume they could be compromised:

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Check if from content script
  if (sender.tab) {
    // Validate data from web page context
    if (!isValidData(message.data)) {
      sendResponse({ error: 'Invalid data' });
      return;
    }
  }
  
  // Limit privileged operations
  if (message.action === 'DELETE_ALL_DATA') {
    // Require user confirmation or additional auth
    return;
  }
});
```

### Message Type Constants

```javascript
// constants.js
export const MessageTypes = {
  GET_DATA: 'GET_DATA',
  SET_DATA: 'SET_DATA',
  DELETE_DATA: 'DELETE_DATA',
  NOTIFY: 'NOTIFY',
  ERROR: 'ERROR'
};

// background.js
import { MessageTypes } from './constants.js';

chrome.runtime.onMessage.addListener((message) => {
  switch (message.type) {
    case MessageTypes.GET_DATA:
      return handleGetData(message.payload);
    case MessageTypes.SET_DATA:
      return handleSetData(message.payload);
    default:
      throw new Error(`Unknown message type: ${message.type}`);
  }
});
```

## Message Size Limits

- Maximum message size: **64 MiB**
- For large data, use `chrome.storage` or split into chunks

```javascript
// Split large messages
async function sendLargeData(data, chunkSize = 1024 * 1024) {
  const chunks = splitIntoChunks(JSON.stringify(data), chunkSize);
  const totalChunks = chunks.length;
  
  for (let i = 0; i < chunks.length; i++) {
    await chrome.runtime.sendMessage({
      type: 'CHUNK',
      chunk: chunks[i],
      index: i,
      total: totalChunks
    });
  }
}
```
