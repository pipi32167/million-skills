# Testing Reference

## Table of Contents

- [Development Mode](#development-mode)
- [Unit Testing](#unit-testing)
- [E2E Testing](#e2e-testing)
- [Debugging Techniques](#debugging-techniques)

## Development Mode

### Loading Unpacked Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select extension directory

### Extension IDs

```javascript
// Get extension ID
console.log(chrome.runtime.id);

// Extension ID format: aaaaaaaaaaaaaaaaaaaaaaa_aaaaaaa
// First 32 chars: public key hash
// Last 7 chars: version
```

### Extension Pages

| Page | URL |
|------|-----|
| Extensions | `chrome://extensions/` |
| Service Worker | `chrome://extensions/?id=ID` → click "service worker" |
| Storage | DevTools → Application → Storage |

## Unit Testing

### Mocking Chrome APIs

```javascript
// __mocks__/chrome.js
global.chrome = {
  storage: {
    local: {
      get: vi.fn(),
      set: vi.fn(),
      remove: vi.fn()
    },
    sync: {
      get: vi.fn(),
      set: vi.fn()
    }
  },
  tabs: {
    query: vi.fn(),
    sendMessage: vi.fn()
  },
  runtime: {
    sendMessage: vi.fn(),
    onMessage: {
      addListener: vi.fn()
    }
  }
};
```

### Testing Storage Operations

```javascript
// storage.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { saveSettings, loadSettings } from './storage.js';

describe('Storage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  it('should save settings', async () => {
    const settings = { theme: 'dark' };
    await saveSettings(settings);
    
    expect(chrome.storage.sync.set).toHaveBeenCalledWith(settings);
  });
  
  it('should load settings', async () => {
    const mockSettings = { theme: 'light' };
    chrome.storage.sync.get.mockResolvedValue(mockSettings);
    
    const result = await loadSettings();
    expect(result).toEqual(mockSettings);
  });
});
```

### Testing Message Handlers

```javascript
// background.test.js
describe('Message Handler', () => {
  it('should handle GET_DATA message', async () => {
    const message = { action: 'GET_DATA', key: 'test' };
    const sender = { id: chrome.runtime.id };
    const sendResponse = vi.fn();
    
    chrome.storage.local.get.mockResolvedValue({ test: 'value' });
    
    const listener = chrome.runtime.onMessage.addListener.mock.calls[0][0];
    const result = listener(message, sender, sendResponse);
    
    expect(result).toBe(true); // Async response
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(sendResponse).toHaveBeenCalledWith({
      success: true,
      data: 'value'
    });
  });
});
```

## E2E Testing

### Using Puppeteer

```javascript
// e2e/extension.test.js
import puppeteer from 'puppeteer';
import path from 'path';

const EXTENSION_PATH = path.resolve('./dist');
const EXTENSION_ID = 'your-extension-id';

describe('Extension E2E', () => {
  let browser;
  let page;
  
  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
        '--no-sandbox'
      ]
    });
  });
  
  afterAll(async () => {
    await browser.close();
  });
  
  beforeEach(async () => {
    page = await browser.newPage();
    await page.goto('https://example.com');
  });
  
  afterEach(async () => {
    await page.close();
  });
  
  it('should open popup', async () => {
    const extensionPage = await openExtensionPopup(browser, EXTENSION_ID);
    
    const title = await extensionPage.$eval('.header', el => el.textContent);
    expect(title).toBe('Extension Name');
  });
  
  it('should inject content script', async () => {
    const result = await page.evaluate(() => {
      return document.querySelector('.extension-element')?.textContent;
    });
    
    expect(result).toBe('Injected content');
  });
});

async function openExtensionPopup(browser, extensionId) {
  const popupUrl = `chrome-extension://${extensionId}/popup.html`;
  const page = await browser.newPage();
  await page.goto(popupUrl);
  return page;
}
```

### Testing Content Script

```javascript
it('should extract page data', async () => {
  await page.setContent(`
    <html>
      <body>
        <h1 class="title">Test Title</h1>
        <p class="content">Test content</p>
      </body>
    </html>
  `);
  
  // Trigger content script
  await page.evaluate(() => {
    chrome.runtime.sendMessage({ action: 'EXTRACT' });
  });
  
  // Verify extraction
  const extracted = await page.evaluate(() => {
    return window.extractedData;
  });
  
  expect(extracted.title).toBe('Test Title');
});
```

## Debugging Techniques

### Console Logging

```javascript
// Use groups for better organization
console.group('Extension Init');
console.log('Loading config...');
console.log('Registering events...');
console.groupEnd();

// Use appropriate log levels
console.debug('Debug info');     // Verbose
console.log('General info');     // Info
console.warn('Warning');         // Warnings
console.error('Error');          // Errors
```

### Conditional Breakpoints

```javascript
// In your code
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // DevTools will break here when condition is met
  if (changeInfo.status === 'complete' && tab.url.includes('example.com')) {
    debugger; // Conditional breakpoint
  }
});
```

### Performance Profiling

```javascript
// Mark start/end of operations
performance.mark('operation-start');

// ... operation code

performance.mark('operation-end');
performance.measure('operation', 'operation-start', 'operation-end');

// Get measurements
const entries = performance.getEntriesByType('measure');
console.log('Operation took:', entries[0].duration, 'ms');
```

### Storage Inspection

```javascript
// Log all storage contents
async function debugStorage() {
  const local = await chrome.storage.local.get(null);
  const sync = await chrome.storage.sync.get(null);
  const session = await chrome.storage.session.get(null);
  
  console.table({
    local: Object.keys(local).length + ' keys',
    sync: Object.keys(sync).length + ' keys',
    session: Object.keys(session).length + ' keys'
  });
  
  console.log('Local:', local);
  console.log('Sync:', sync);
  console.log('Session:', session);
}
```

### Network Debugging

```javascript
// Log all network requests
chrome.webRequest.onCompleted.addListener(
  (details) => {
    console.log('Request completed:', {
      url: details.url,
      method: details.method,
      status: details.statusCode,
      time: details.timeStamp
    });
  },
  { urls: ['<all_urls>'] }
);
```

### Error Tracking

```javascript
// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', {
    message: event.message,
    filename: event.filename,
    line: event.lineno,
    column: event.colno,
    error: event.error?.stack
  });
});

// Unhandled promise rejection
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled rejection:', event.reason);
});
```

### DevTools Tips

1. **Service Worker Inspector**
   - Go to `chrome://extensions`
   - Find your extension
   - Click "service worker" link
   - Full DevTools available

2. **Extension Storage Viewer**
   - Open DevTools for any extension page
   - Go to Application → Storage
   - View `chrome.storage` contents

3. **Network Throttling**
   - Test slow connections
   - Test offline behavior

4. **Console Filtering**
   - Use `-extension` to filter out extension noise
   - Use `[filename]` to find specific logs

## Testing Checklist

- [ ] Unit tests for core functions
- [ ] Mock Chrome APIs correctly
- [ ] E2E tests for user flows
- [ ] Test error handling
- [ ] Test with different Chrome versions
- [ ] Test permission scenarios
- [ ] Test storage quotas
- [ ] Test Service Worker lifecycle
- [ ] Test content script injection
- [ ] Verify popup functionality
