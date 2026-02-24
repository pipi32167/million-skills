# Manifest V3 Reference

## Table of Contents

- [Core Changes from MV2](#core-changes-from-mv2)
- [Basic Configuration](#basic-configuration)
- [Permissions](#permissions)
- [Migration Guide](#migration-guide)

## Core Changes from MV2

| Feature | MV2 | MV3 |
|---------|-----|-----|
| Background script | Persistent background page | Non-persistent Service Worker |
| Network modification | `webRequest` (blocking) | `declarativeNetRequest` (declarative) |
| Remote code | Allowed | **Prohibited** |
| Content Security Policy | Relaxed | Stricter |
| Promises | Callbacks mostly | Native Promise support |

## Basic Configuration

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "description": "Extension description",
  
  "permissions": [
    "storage",
    "activeTab",
    "scripting",
    "alarms"
  ],
  
  "host_permissions": [
    "https://*.example.com/*"
  ],
  
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "css": ["content.css"],
      "run_at": "document_idle"
    }
  ],
  
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  
  "web_accessible_resources": [
    {
      "resources": ["assets/*"],
      "matches": ["<all_urls>"]
    }
  ],
  
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

## Permissions

### Required vs Optional

```json
{
  "permissions": [
    "storage",
    "activeTab"
  ],
  "optional_permissions": [
    "history",
    "bookmarks"
  ],
  "host_permissions": [
    "https://example.com/*"
  ]
}
```

### Requesting Optional Permissions

```javascript
// Request at runtime
const granted = await chrome.permissions.request({
  permissions: ['history'],
  origins: ['https://example.com/*']
});

if (granted) {
  // Use the permission
}
```

### Permission Warning Guidelines

Some permissions trigger warnings that may deter users:

| Permission | Warning Message |
|------------|-----------------|
| `<all_urls>` | "Read and change all your data on all websites" |
| `tabs` | "Read your browsing history" |
| `webNavigation` | "Read your browsing history" |

**Best Practice**: Use `activeTab` instead of broad host permissions when possible.

## Migration Guide

### 1. Update manifest version

```json
{
  "manifest_version": 3
}
```

### 2. Convert background page to Service Worker

```json
// MV2
{
  "background": {
    "scripts": ["background.js"],
    "persistent": false
  }
}

// MV3
{
  "background": {
    "service_worker": "background.js",
    "type": "module"
  }
}
```

### 3. Update API calls to use Promises

```javascript
// MV2 (callback)
chrome.tabs.query({ active: true }, (tabs) => {
  console.log(tabs);
});

// MV3 (Promise)
const tabs = await chrome.tabs.query({ active: true });
console.log(tabs);
```

### 4. Replace webRequest with declarativeNetRequest

```json
{
  "declarative_net_request": {
    "rule_resources": [
      {
        "id": "ruleset_1",
        "enabled": true,
        "path": "rules.json"
      }
    ]
  }
}
```

```json
// rules.json
[
  {
    "id": 1,
    "priority": 1,
    "action": {
      "type": "block"
    },
    "condition": {
      "urlFilter": "*example.com/ads/*",
      "resourceTypes": ["script"]
    }
  }
]
```

### 5. Remove remote code

```javascript
// ❌ Not allowed in MV3
const code = fetch('https://example.com/code.js');
eval(code);

// ✅ Bundle all code with the extension
import { functionName } from './local-module.js';
```

## Version Format

Use semantic versioning:

```json
{
  "version": "1.2.3"
}
```

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes
