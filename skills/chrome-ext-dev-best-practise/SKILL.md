---
name: chrome-ext-dev-best-practise
description: Chrome extension development best practices for Manifest V3. Use when developing, reviewing, or debugging Chrome extensions. Covers architecture (Service Worker, Content Script, Popup), messaging patterns, storage strategies, security guidelines, and performance optimization.
---

# Chrome Extension Development Best Practices

## Overview

This skill provides comprehensive best practices for Chrome extension development using Manifest V3 (MV3).

## Core Architecture

Chrome extensions consist of three main components:

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
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Runs In | Primary Use |
|-----------|---------|-------------|
| **Service Worker** | Extension context | Background logic, event handling, API calls |
| **Content Script** | Web page context | DOM manipulation, page interaction |
| **Popup** | Extension context | User interface, quick actions |

### Service Worker Key Points

- **Non-persistent**: Can be terminated after ~5 minutes of inactivity
- **Stateless**: Don't rely on global variables for state
- **Use Storage**: Persist data with `chrome.storage` APIs

```javascript
// ✅ Good: Use storage for state
chrome.storage.local.set({ key: value });

// ❌ Bad: Global variables are lost on termination
let globalState = {}; // Don't do this
```

## Quick Reference

### When to Use Which Reference

| Task | Reference |
|------|-----------|
| Manifest V3 configuration | [references/manifest-v3.md](references/manifest-v3.md) |
| Architecture patterns | [references/architecture.md](references/architecture.md) |
| Message passing between components | [references/messaging.md](references/messaging.md) |
| Storage API usage | [references/storage.md](references/storage.md) |
| Security guidelines | [references/security.md](references/security.md) |
| Performance optimization | [references/performance.md](references/performance.md) |
| UI/Popup design | [references/ui-design.md](references/ui-design.md) |
| Testing & debugging | [references/testing.md](references/testing.md) |

## Common Patterns

### 1. Minimal Permission Principle

```json
// ❌ Bad: Over-permissioned
{
  "permissions": ["tabs", "activeTab", "scripting", "storage", "webNavigation"],
  "host_permissions": ["<all_urls>"]
}

// ✅ Good: Minimal permissions
{
  "permissions": ["activeTab", "scripting"],
  "host_permissions": ["https://example.com/*"]
}
```

### 2. Async Message Handling

```javascript
// background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      const result = await handleMessage(message);
      sendResponse({ success: true, data: result });
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  })();
  return true; // Keep channel open for async
});
```

### 3. Storage Selection

| Use Case | Storage Area |
|----------|--------------|
| User settings (sync across devices) | `chrome.storage.sync` |
| Large data, cache | `chrome.storage.local` |
| Sensitive data, session only | `chrome.storage.session` |
| Enterprise policies | `chrome.storage.managed` |

## Project Templates

Use templates in `assets/templates/` as starting points:

- `basic/` - Minimal MV3 extension template
- `with-react/` - React-based popup template
- `with-content-script/` - Content script injection template

## Security Checklist

- [ ] Implement Content Security Policy (CSP)
- [ ] Validate all messages from content scripts
- [ ] Use HTTPS for all network requests
- [ ] Sanitize user input before DOM insertion
- [ ] Store sensitive tokens in `chrome.storage.session`
- [ ] Review permissions before each release

## Performance Checklist

- [ ] Use `chrome.alarms` instead of `setInterval`
- [ ] Batch storage operations
- [ ] Clean up event listeners
- [ ] Use `requestIdleCallback` for non-urgent tasks
- [ ] Avoid `unload` handlers (breaks bfcache)

## Migration from MV2

Key changes when migrating from Manifest V2:

1. Replace `background.scripts` with `service_worker`
2. Migrate `webRequest` blocking to `declarativeNetRequest`
3. Remove remote code execution
4. Update API calls (many now return Promises)
5. Handle CSP restrictions

See [references/manifest-v3.md](references/manifest-v3.md) for detailed migration guide.
