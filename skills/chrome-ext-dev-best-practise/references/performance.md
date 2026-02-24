# Performance Reference

## Table of Contents

- [Service Worker Optimization](#service-worker-optimization)
- [Memory Management](#memory-management)
- [Content Script Performance](#content-script-performance)
- [Storage Optimization](#storage-optimization)

## Service Worker Optimization

### Use Alarms Instead of Intervals

```javascript
// ❌ Bad: setInterval doesn't work well with Service Workers
setInterval(() => {
  checkForUpdates();
}, 60000);

// ✅ Good: Use chrome.alarms
chrome.alarms.create('check-updates', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'check-updates') {
    checkForUpdates();
  }
});
```

### Lazy Loading

```javascript
// Load heavy modules only when needed
async function performHeavyTask() {
  const { heavyModule } = await import('./heavy-module.js');
  return heavyModule.process();
}
```

### Debounce and Throttle

```javascript
function debounce(fn, ms) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), ms);
  };
}

function throttle(fn, ms) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last > ms) {
      last = now;
      fn(...args);
    }
  };
}

// Usage
const debouncedSave = debounce(saveData, 500);
chrome.storage.onChanged.addListener((changes) => {
  debouncedSave(changes);
});
```

### Batch Operations

```javascript
class MessageBatcher {
  constructor(processFn, options = {}) {
    this.batch = [];
    this.processFn = processFn;
    this.batchSize = options.batchSize || 10;
    this.interval = options.interval || 100;
    this.startTimer();
  }
  
  add(item) {
    this.batch.push(item);
    if (this.batch.length >= this.batchSize) {
      this.flush();
    }
  }
  
  async flush() {
    if (this.batch.length === 0) return;
    const items = this.batch.splice(0);
    await this.processFn(items);
  }
  
  startTimer() {
    setInterval(() => this.flush(), this.interval);
  }
}

// Usage
const batcher = new MessageBatcher(async (messages) => {
  await chrome.storage.local.set({
    'messages:batch': messages
  });
});

// Add messages as they arrive
batcher.add(newMessage);
```

## Memory Management

### Remove Event Listeners

```javascript
// ❌ Bad: Listener stays forever
chrome.tabs.onUpdated.addListener(handleUpdate);

// ✅ Good: Remove when no longer needed
function handleUpdate(tabId, changeInfo) {
  if (changeInfo.status === 'complete') {
    processTab(tabId);
    chrome.tabs.onUpdated.removeListener(handleUpdate);
  }
}
chrome.tabs.onUpdated.addListener(handleUpdate);

// ✅ Good: Use once option if available
element.addEventListener('click', handler, { once: true });
```

### Weak References

```javascript
// Use WeakMap/WeakSet for caches that should not prevent GC
const cache = new WeakMap();

function processElement(element) {
  if (cache.has(element)) {
    return cache.get(element);
  }
  
  const result = expensiveOperation(element);
  cache.set(element, result);
  return result;
}
// When element is removed from DOM, cache entry can be GC'd
```

### Clean Up Observers

```javascript
// content.js
const observer = new MutationObserver(handleMutations);
observer.observe(document.body, { childList: true });

// Clean up on unload
window.addEventListener('beforeunload', () => {
  observer.disconnect();
});

// Or use AbortController
const controller = new AbortController();
observer.observe(target, { signal: controller.signal });
// Later: controller.abort();
```

## Content Script Performance

### Avoid Blocking Page Load

```javascript
// ❌ Bad: Heavy processing blocks page load
document.addEventListener('DOMContentLoaded', heavyProcessing);

// ✅ Good: Use requestIdleCallback
requestIdleCallback(() => {
  heavyProcessing();
}, { timeout: 2000 });

// ✅ Good: Defer non-critical work
if ('requestIdleCallback' in window) {
  requestIdleCallback(nonCriticalWork);
} else {
  setTimeout(nonCriticalWork, 1);
}
```

### Intersection Observer for Lazy Loading

```javascript
// Load widgets only when visible
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      loadWidget(entry.target);
      observer.unobserve(entry.target);
    }
  });
});

document.querySelectorAll('.lazy-widget').forEach(el => {
  observer.observe(el);
});
```

### Minimize DOM Operations

```javascript
// ❌ Bad: Multiple reflows
for (const item of items) {
  const el = document.createElement('div');
  el.textContent = item.text;
  container.appendChild(el); // Reflow on each iteration
}

// ✅ Good: DocumentFragment
const fragment = document.createDocumentFragment();
for (const item of items) {
  const el = document.createElement('div');
  el.textContent = item.text;
  fragment.appendChild(el);
}
container.appendChild(fragment); // Single reflow

// ✅ Good: Clone template
const template = document.getElementById('item-template');
const fragment = document.createDocumentFragment();
for (const item of items) {
  const clone = template.content.cloneNode(true);
  clone.querySelector('.text').textContent = item.text;
  fragment.appendChild(clone);
}
container.appendChild(fragment);
```

### Avoid unload Handlers

```javascript
// ❌ Bad: Breaks bfcache (back/forward cache)
window.addEventListener('unload', () => {
  saveState();
});

// ✅ Good: Use pagehide or visibilitychange
window.addEventListener('pagehide', () => {
  saveState();
});

// ✅ Good: Use visibility API
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    saveState();
  }
});
```

## Storage Optimization

### Batch Storage Operations

```javascript
// ❌ Bad: Multiple storage calls
for (const key of keys) {
  await chrome.storage.local.set({ [key]: data[key] });
}

// ✅ Good: Single batch operation
await chrome.storage.local.set(
  keys.reduce((acc, key) => {
    acc[key] = data[key];
    return acc;
  }, {})
);
```

### Cache Frequently Accessed Data

```javascript
class StorageCache {
  constructor() {
    this.cache = new Map();
    this.ttl = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes
  }
  
  async get(key, ttl = this.defaultTTL) {
    const now = Date.now();
    
    if (this.cache.has(key) && this.ttl.get(key) > now) {
      return this.cache.get(key);
    }
    
    const value = await chrome.storage.local.get(key);
    this.cache.set(key, value[key]);
    this.ttl.set(key, now + ttl);
    
    return value[key];
  }
  
  async set(key, value, ttl = this.defaultTTL) {
    this.cache.set(key, value);
    this.ttl.set(key, Date.now() + ttl);
    await chrome.storage.local.set({ [key]: value });
  }
  
  invalidate(key) {
    this.cache.delete(key);
    this.ttl.delete(key);
  }
}
```

### Compress Large Data

```javascript
// For data > 1KB, consider compression
async function compressAndStore(key, data) {
  const json = JSON.stringify(data);
  
  if (json.length > 1024) {
    // Use compression library like lz-string
    const compressed = LZString.compress(json);
    await chrome.storage.local.set({
      [`${key}:compressed`]: true,
      [key]: compressed
    });
  } else {
    await chrome.storage.local.set({ [key]: data });
  }
}
```

## Performance Checklist

- [ ] Use `chrome.alarms` instead of `setInterval`
- [ ] Remove event listeners when done
- [ ] Batch storage operations
- [ ] Use `requestIdleCallback` for non-urgent work
- [ ] Avoid `unload` event listeners
- [ ] Use Intersection Observer for lazy loading
- [ ] Minimize DOM operations with DocumentFragment
- [ ] Lazy load heavy modules
- [ ] Implement caching for storage reads
- [ ] Monitor memory usage in DevTools
