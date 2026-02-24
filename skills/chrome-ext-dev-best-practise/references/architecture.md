# Architecture Reference

## Table of Contents

- [Component Overview](#component-overview)
- [Service Worker](#service-worker)
- [Content Script](#content-script)
- [Popup](#popup)
- [Communication Flow](#communication-flow)

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Extension Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Service    │◄──►│   Content    │◄──►│    Popup     │  │
│  │   Worker     │    │   Script     │    │              │  │
│  │              │    │              │    │              │  │
│  │ • Background │    │ • Page DOM   │    │ • User UI    │  │
│  │ • Events     │    │ • Injection  │    │ • Settings   │  │
│  │ • API calls  │    │ • Extraction │    │ • Actions    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│          │                    │                   │        │
│          └────────────────────┴───────────────────┘        │
│                         │                                  │
│              ┌────────────────────┐                        │
│              │   chrome.storage   │                        │
│              │   chrome.runtime   │                        │
│              └────────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Service Worker

### Key Characteristics

- **Non-persistent**: Can be terminated after ~5 minutes
- **Event-driven**: Only runs when handling events
- **No DOM access**: Cannot access `window` or `document`

### State Management

```javascript
// ❌ Bad: Global variables are lost
let cache = {};

// ✅ Good: Use storage API
async function saveState(key, value) {
  await chrome.storage.local.set({ [key]: value });
}

async function getState(key) {
  const result = await chrome.storage.local.get(key);
  return result[key];
}
```

### Event Handling

```javascript
// background.js

// Handle extension icon click
chrome.action.onClicked.addListener(handleActionClick);

// Handle tab updates
chrome.tabs.onUpdated.addListener(handleTabUpdate);

// Handle messages
chrome.runtime.onMessage.addListener(handleMessage);

// Handle alarms (use instead of setInterval)
chrome.alarms.create('refresh', { periodInMinutes: 5 });
chrome.alarms.onAlarm.addListener(handleAlarm);
```

### Keeping Service Worker Active

```javascript
// Use alarms for periodic tasks
chrome.alarms.create('keep-alive', { periodInMinutes: 4 });

// Avoid long-running operations
// Split work into chunks if needed
```

## Content Script

### Execution Worlds

```javascript
// Isolated world (default) - separate from page JS
chrome.scripting.executeScript({
  target: { tabId },
  world: 'ISOLATED',
  func: () => {
    // Cannot access page's JavaScript variables
  }
});

// Main world - shared with page JS
chrome.scripting.executeScript({
  target: { tabId },
  world: 'MAIN',
  func: () => {
    // Can access page's JavaScript
    // Risk of conflicts
  }
});
```

### Communication with Page

```javascript
// content.js (ISOLATED world)

// Inject script into main world
const script = document.createElement('script');
script.src = chrome.runtime.getURL('page-script.js');
script.onload = () => script.remove();
document.head.appendChild(script);

// Use CustomEvent for communication
window.addEventListener('fromPage', (event) => {
  console.log('From page:', event.detail);
});

window.dispatchEvent(new CustomEvent('fromExtension', {
  detail: { message: 'Hello' }
}));
```

### Memory Management

```javascript
// Clean up observers on page unload
const observer = new MutationObserver(handleMutations);
observer.observe(document.body, { childList: true });

window.addEventListener('beforeunload', () => {
  observer.disconnect();
});
```

## Popup

### Lifecycle

- Created when user clicks extension icon
- Destroyed when user clicks outside
- Cannot communicate directly with content scripts

### Pattern: Load data on open

```javascript
// popup.js
document.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const data = await chrome.storage.local.get('data');
  renderUI(data, tab);
});
```

## Communication Flow

### Component Communication Matrix

| From ↓ / To → | Service Worker | Content Script | Popup |
|---------------|----------------|----------------|-------|
| **Service Worker** | N/A | `tabs.sendMessage()` | N/A |
| **Content Script** | `runtime.sendMessage()` | N/A | N/A |
| **Popup** | `runtime.sendMessage()` | `tabs.sendMessage()` | N/A |

### Typical Workflows

**Content Script → Background:**
```javascript
// content.js
const response = await chrome.runtime.sendMessage({
  action: 'fetchData',
  url: location.href
});
```

**Background → Content Script:**
```javascript
// background.js
await chrome.tabs.sendMessage(tabId, {
  action: 'updateUI',
  data: result
});
```

**Popup → Content Script:**
```javascript
// popup.js
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
await chrome.tabs.sendMessage(tab.id, { action: 'scanPage' });
```
