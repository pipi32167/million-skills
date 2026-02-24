# Security Reference

## Table of Contents

- [Content Security Policy](#content-security-policy)
- [XSS Prevention](#xss-prevention)
- [Message Security](#message-security)
- [Data Protection](#data-protection)
- [Permission Security](#permission-security)

## Content Security Policy

### Default CSP

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### Relaxed CSP (if needed)

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self' 'unsafe-eval'; object-src 'self'",
    "sandbox": "sandbox allow-scripts; script-src 'self' 'unsafe-eval'"
  }
}
```

**Note**: Avoid `'unsafe-inline'` and `'unsafe-eval'` when possible.

## XSS Prevention

### DOM Insertion

```javascript
// ❌ Dangerous: innerHTML with user input
element.innerHTML = userInput;

// ✅ Safe: Use textContent
element.textContent = userInput;

// ✅ Safe: Create elements
const div = document.createElement('div');
div.textContent = userInput;
container.appendChild(div);

// ✅ Safe: Sanitize HTML (using DOMPurify)
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### URL Validation

```javascript
function isValidUrl(url) {
  try {
    const parsed = new URL(url);
    // Only allow http/https
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

// Usage
if (isValidUrl(userUrl)) {
  window.open(userUrl, '_blank');
}
```

### Eval Prevention

```javascript
// ❌ Never use eval
eval(userCode);

// ❌ Never use Function constructor
new Function(userCode)();

// ❌ Never use setTimeout with strings
setTimeout('alert("xss")', 100);

// ✅ Use JSON.parse for data
const data = JSON.parse(userJson);

// ✅ Use safe alternatives
const allowedFunctions = {
  'add': (a, b) => a + b,
  'multiply': (a, b) => a * b
};

const result = allowedFunctions[operation]?.(a, b);
```

## Message Security

### Validate Message Origin

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Verify sender is the extension
  if (!sender.id || sender.id !== chrome.runtime.id) {
    console.warn('Invalid sender:', sender);
    return;
  }
  
  // Verify message structure
  if (!message || typeof message !== 'object') {
    return;
  }
  
  // Verify action is allowed
  const allowedActions = ['GET_DATA', 'SET_DATA'];
  if (!allowedActions.includes(message.action)) {
    return;
  }
  
  // Process validated message
});
```

### Content Script Distrust

Treat content scripts as potentially compromised:

```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.tab) {
    // Message from content script (web page context)
    // Sanitize all data from content scripts
    const sanitizedData = sanitizeInput(message.data);
    
    // Limit privileged operations
    if (message.action === 'DELETE_ALL') {
      // Require additional confirmation
      return;
    }
  }
});
```

## Data Protection

### Secure Token Storage

```javascript
// Store sensitive tokens in session storage
await chrome.storage.session.set({
  'auth:token': temporaryToken
});

// Session storage is cleared when browser restarts
// For long-term sensitive data, use Offscreen API
```

### Offscreen API for Sensitive Operations

```javascript
// manifest.json
{
  "permissions": ["offscreen"]
}

// Create offscreen document
await chrome.offscreen.createDocument({
  url: 'offscreen.html',
  reasons: ['WORKERS'],
  justification: 'Perform encryption'
});

// offscreen.js handles sensitive operations
```

### Encryption Example

```javascript
// Encrypt data before storing
async function encryptData(data, key) {
  const encoder = new TextEncoder();
  const encoded = encoder.encode(JSON.stringify(data));
  
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded
  );
  
  return { iv, data: Array.from(new Uint8Array(encrypted)) };
}

async function decryptData(encrypted, key) {
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(encrypted.iv) },
    key,
    new Uint8Array(encrypted.data)
  );
  
  const decoder = new TextDecoder();
  return JSON.parse(decoder.decode(decrypted));
}
```

## Permission Security

### Principle of Least Privilege

```json
// ❌ Over-permissioned
{
  "permissions": [
    "tabs",
    "activeTab", 
    "scripting",
    "storage",
    "webNavigation",
    "history",
    "cookies"
  ],
  "host_permissions": ["<all_urls>"]
}

// ✅ Minimal permissions
{
  "permissions": ["activeTab", "scripting"],
  "host_permissions": ["https://example.com/*"]
}
```

### Optional Permissions

```javascript
// Request only when needed
async function requestHistoryPermission() {
  const granted = await chrome.permissions.request({
    permissions: ['history']
  });
  
  if (granted) {
    // Use history API
    const history = await chrome.history.search({ text: '' });
    return history;
  }
  
  return null;
}
```

### Permission Warnings

Be aware of warnings that may deter users:

| Permission | Warning |
|------------|---------|
| `<all_urls>` | "Read and change all your data on all websites" |
| `tabs` | "Read your browsing history" |
| `webNavigation` | "Read your browsing history" |
| `cookies` | "Read and change all your data on websites you visit" |

**Mitigation**: Use `activeTab` instead of broad host permissions when possible.

## Security Checklist

- [ ] Implement strict CSP
- [ ] Validate all external input
- [ ] Sanitize DOM insertions
- [ ] Verify message origins
- [ ] Use session storage for sensitive data
- [ ] Request minimal permissions
- [ ] Use HTTPS for all network requests
- [ ] Implement proper error handling
- [ ] Regular security audits
- [ ] Keep dependencies updated
