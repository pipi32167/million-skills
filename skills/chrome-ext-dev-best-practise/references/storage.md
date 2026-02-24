# Storage Reference

## Table of Contents

- [Storage Areas](#storage-areas)
- [Usage Examples](#usage-examples)
- [Quota Management](#quota-management)
- [Change Monitoring](#change-monitoring)

## Storage Areas

| Area | Size Limit | Persistent | Sync | Use Case |
|------|------------|------------|------|----------|
| `local` | 10 MB | Yes | No | Cache, large data |
| `sync` | 100 KB / 512 items | Yes | Yes | User settings |
| `session` | 10 MB | No | No | Sensitive data, temp state |
| `managed` | N/A (read-only) | Yes | Enterprise | Admin policies |

## Usage Examples

### Basic Operations

```javascript
// Set values
await chrome.storage.local.set({
  'user:preferences': { theme: 'dark' },
  'cache:lastUpdate': Date.now()
});

// Get values
const result = await chrome.storage.local.get([
  'user:preferences',
  'cache:lastUpdate'
]);

// Remove values
await chrome.storage.local.remove('cache:lastUpdate');

// Clear all
await chrome.storage.local.clear();
```

### Sync Storage

```javascript
// User settings - sync across devices
await chrome.storage.sync.set({
  'settings:theme': 'dark',
  'settings:notifications': true,
  'settings:shortcut': 'Ctrl+Shift+Y'
});

// Get all settings
const settings = await chrome.storage.sync.get(null);
```

**Sync Limits:**
- Total: ~100 KB
- Per item: 8 KB
- Max items: 512
- Write rate: 2/sec (120/min)

### Session Storage

```javascript
// Temporary data, cleared when browser restarts
await chrome.storage.session.set({
  'auth:token': temporaryToken,
  'session:startTime': Date.now()
});

// Good for sensitive data that shouldn't persist
```

### Access Level Control

```javascript
// Restrict access to content scripts
await chrome.storage.local.setAccessLevel({
  accessLevel: 'TRUSTED_CONTEXTS'
});

// Values:
// - 'TRUSTED_CONTEXTS': Extension only
// - 'TRUSTED_AND_UNTRUSTED_CONTEXTS': Extension + content scripts
```

## Quota Management

### Check Usage

```javascript
// Get bytes in use
const bytes = await chrome.storage.local.getBytesInUse();
const bytesSync = await chrome.storage.sync.getBytesInUse();

// Check specific keys
const keyBytes = await chrome.storage.local.getBytesInUse([
  'key1',
  'key2'
]);
```

### Compression

```javascript
// For large data, consider compression
function compressData(data) {
  const json = JSON.stringify(data);
  // Use lz-string or similar for compression
  return LZString.compressToUTF16(json);
}

function decompressData(compressed) {
  const json = LZString.decompressFromUTF16(compressed);
  return JSON.parse(json);
}
```

### Chunking Large Data

```javascript
async function saveLargeData(key, data, chunkSize = 8000) {
  const json = JSON.stringify(data);
  const chunks = [];
  
  for (let i = 0; i < json.length; i += chunkSize) {
    chunks.push(json.slice(i, i + chunkSize));
  }
  
  // Save metadata + chunks
  await chrome.storage.local.set({
    [`${key}:meta`]: { chunks: chunks.length, total: json.length },
    ...chunks.reduce((acc, chunk, i) => {
      acc[`${key}:chunk:${i}`] = chunk;
      return acc;
    }, {})
  });
}

async function loadLargeData(key) {
  const meta = await chrome.storage.local.get(`${key}:meta`);
  if (!meta[`${key}:meta`]) return null;
  
  const { chunks } = meta[`${key}:meta`];
  const chunkKeys = Array.from(
    { length: chunks },
    (_, i) => `${key}:chunk:${i}`
  );
  
  const chunkData = await chrome.storage.local.get(chunkKeys);
  const json = chunkKeys.map(k => chunkData[k]).join('');
  
  return JSON.parse(json);
}
```

## Change Monitoring

```javascript
// Listen for storage changes
chrome.storage.onChanged.addListener((changes, areaName) => {
  for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(`Storage change in ${areaName}:`, {
      key,
      oldValue,
      newValue
    });
    
    // React to specific changes
    if (key === 'settings:theme') {
      applyTheme(newValue);
    }
  }
});
```

### Cross-Component Sync

```javascript
// options.js - Save settings
const saveSettings = debounce(async (settings) => {
  await chrome.storage.sync.set({ 'settings:data': settings });
}, 500);

// background.js - React to changes
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'sync' && changes['settings:data']) {
    const newSettings = changes['settings:data'].newValue;
    applySettings(newSettings);
  }
});

// popup.js - Load settings on open
async function loadSettings() {
  const { 'settings:data': settings } = await chrome.storage.sync.get('settings:data');
  return settings;
}
```

## Caching Pattern

```javascript
class StorageCache {
  constructor() {
    this.cache = new Map();
    this.initPromise = this.init();
  }
  
  async init() {
    const all = await chrome.storage.local.get(null);
    for (const [key, value] of Object.entries(all)) {
      this.cache.set(key, value);
    }
  }
  
  async get(key) {
    await this.initPromise;
    return this.cache.get(key);
  }
  
  async set(key, value) {
    this.cache.set(key, value);
    await chrome.storage.local.set({ [key]: value });
  }
  
  async remove(key) {
    this.cache.delete(key);
    await chrome.storage.local.remove(key);
  }
}

const cache = new StorageCache();
```

## Best Practices

1. **Use namespaced keys**: `'user:preferences'`, `'cache:data'`
2. **Batch operations**: Minimize storage calls
3. **Handle quota errors**: Wrap in try-catch
4. **Don't store sensitive data in sync**: Use `session` or encrypt
5. **Clean up old data**: Implement TTL for cache entries
