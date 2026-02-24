# UI Design Reference

## Table of Contents

- [Popup Design](#popup-design)
- [Options Page](#options-page)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Material Design Guidelines](#material-design-guidelines)

## Popup Design

### Fixed Dimensions

```html
<!-- popup.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    /* Fixed size prevents layout shifts */
    body {
      width: 350px;
      min-height: 400px;
      margin: 0;
      padding: 16px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
  </style>
</head>
<body>
  <!-- Content -->
</body>
</html>
```

### Responsive Layout

```html
<style>
  .container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .header {
    font-size: 16px;
    font-weight: 600;
    color: #1a1a1a;
  }
  
  .section {
    padding: 12px;
    background: #f5f5f5;
    border-radius: 8px;
  }
  
  /* Touch-friendly sizes */
  .button {
    padding: 10px 16px;
    min-height: 36px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .button-primary {
    background: #1a73e8;
    color: white;
    border: none;
  }
  
  .button-secondary {
    background: transparent;
    color: #1a73e8;
    border: 1px solid #dadce0;
  }
  
  /* Loading state */
  .loading {
    opacity: 0.6;
    pointer-events: none;
  }
  
  /* Empty state */
  .empty-state {
    text-align: center;
    padding: 32px 16px;
    color: #5f6368;
  }
</style>
```

### Loading States

```javascript
// popup.js
const loadingOverlay = document.getElementById('loading');
const content = document.getElementById('content');

async function loadData() {
  showLoading();
  try {
    const data = await fetchData();
    render(data);
  } catch (error) {
    showError(error);
  } finally {
    hideLoading();
  }
}

function showLoading() {
  loadingOverlay.style.display = 'flex';
  content.classList.add('loading');
}

function hideLoading() {
  loadingOverlay.style.display = 'none';
  content.classList.remove('loading');
}
```

## Options Page

### Auto-Save Pattern

```javascript
// options.js
const settingsInputs = document.querySelectorAll('[data-setting]');

settingsInputs.forEach(input => {
  input.addEventListener('change', async () => {
    const key = input.dataset.setting;
    const value = input.type === 'checkbox' ? input.checked : input.value;
    
    await chrome.storage.sync.set({ [key]: value });
    showToast('Settings saved');
  });
});

// Load saved settings
async function loadSettings() {
  const settings = await chrome.storage.sync.get(null);
  
  Object.entries(settings).forEach(([key, value]) => {
    const input = document.querySelector(`[data-setting="${key}"]`);
    if (input) {
      if (input.type === 'checkbox') {
        input.checked = value;
      } else {
        input.value = value;
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', loadSettings);

// Toast notification
function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.remove(), 2000);
}
```

### Options Page HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Extension Options</title>
  <style>
    body {
      max-width: 600px;
      margin: 40px auto;
      padding: 0 20px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
    }
    
    h1 {
      font-size: 24px;
      margin-bottom: 24px;
    }
    
    .section {
      margin-bottom: 32px;
    }
    
    .section-title {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    
    .field {
      margin-bottom: 16px;
    }
    
    label {
      display: block;
      margin-bottom: 4px;
      font-weight: 500;
    }
    
    input[type="text"],
    input[type="number"],
    select {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #dadce0;
      border-radius: 4px;
      font-size: 14px;
    }
    
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
    
    .description {
      font-size: 12px;
      color: #5f6368;
      margin-top: 4px;
    }
    
    /* Toast notification */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #323232;
      color: white;
      padding: 12px 24px;
      border-radius: 4px;
      animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
      from { transform: translateY(100%); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  </style>
</head>
<body>
  <h1>Extension Settings</h1>
  
  <div class="section">
    <div class="section-title">General</div>
    
    <div class="field">
      <label class="checkbox-label">
        <input type="checkbox" data-setting="enableNotifications">
        Enable notifications
      </label>
      <div class="description">Show desktop notifications for important events</div>
    </div>
    
    <div class="field">
      <label for="theme">Theme</label>
      <select id="theme" data-setting="theme">
        <option value="system">System default</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </div>
  </div>
  
  <script src="options.js"></script>
</body>
</html>
```

## Keyboard Shortcuts

### Manifest Declaration

```json
{
  "commands": {
    "_execute_action": {
      "suggested_key": {
        "default": "Ctrl+Shift+F",
        "mac": "Command+Shift+F"
      },
      "description": "Open extension popup"
    },
    "toggle-feature": {
      "suggested_key": {
        "default": "Ctrl+Shift+Y",
        "mac": "Command+Shift+Y"
      },
      "description": "Toggle main feature"
    },
    "quick-action": {
      "description": "Perform quick action"
    }
  }
}
```

### Handling Commands

```javascript
// background.js
chrome.commands.onCommand.addListener((command) => {
  switch (command) {
    case 'toggle-feature':
      toggleFeature();
      break;
    case 'quick-action':
      performQuickAction();
      break;
  }
});

async function toggleFeature() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.tabs.sendMessage(tab.id, { action: 'TOGGLE' });
}
```

### Shortcut Conflicts

- Avoid common shortcuts (Ctrl+S, Ctrl+C, etc.)
- Use Ctrl+Shift or Alt+Shift combinations
- Allow users to customize shortcuts

## Material Design Guidelines

### Color Palette

```css
:root {
  /* Primary */
  --primary: #1a73e8;
  --primary-dark: #1557b0;
  --primary-light: #8ab4f8;
  
  /* Surface */
  --surface: #ffffff;
  --surface-variant: #f1f3f4;
  --background: #f8f9fa;
  
  /* Text */
  --text-primary: #202124;
  --text-secondary: #5f6368;
  --text-disabled: #9aa0a6;
  
  /* Status */
  --success: #34a853;
  --warning: #fbbc04;
  --error: #ea4335;
}
```

### Elevation

```css
.elevation-1 {
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.3),
              0 1px 3px 1px rgba(60, 64, 67, 0.15);
}

.elevation-2 {
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.3),
              0 2px 6px 2px rgba(60, 64, 67, 0.15);
}

.elevation-3 {
  box-shadow: 0 1px 3px 0 rgba(60, 64, 67, 0.3),
              0 4px 8px 3px rgba(60, 64, 67, 0.15);
}
```

### Spacing Scale

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
}
```

### Accessibility

```css
/* Focus indicators */
button:focus-visible,
a:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* High contrast */
@media (prefers-contrast: high) {
  :root {
    --text-primary: #000000;
    --text-secondary: #333333;
  }
}
```

## Best Practices

1. **Consistent spacing**: Use 4px or 8px grid
2. **Clear hierarchy**: Use font weight and size to indicate importance
3. **Touch targets**: Minimum 36x36px for interactive elements
4. **Loading feedback**: Always show progress for async operations
5. **Error handling**: Display user-friendly error messages
6. **Dark mode**: Support `prefers-color-scheme`
