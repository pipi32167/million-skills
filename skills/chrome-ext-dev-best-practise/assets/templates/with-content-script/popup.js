// Popup script
// Coordinates with content scripts on the active tab

document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Set up buttons
  document.getElementById('extractBtn').addEventListener('click', () => {
    extractData(tab.id);
  });
  
  document.getElementById('highlightBtn').addEventListener('click', () => {
    const selector = document.getElementById('selector').value || 'h1';
    highlightElements(tab.id, selector);
  });
  
  document.getElementById('injectBtn').addEventListener('click', () => {
    injectScript(tab.id);
  });
  
  // Load initial data
  await extractData(tab.id);
});

async function extractData(tabId) {
  showLoading(true);
  
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      action: 'EXTRACT_DATA'
    });
    
    if (response.success) {
      renderData(response.data);
    } else {
      showError(response.error);
    }
  } catch (error) {
    // Content script not loaded
    showError('Content script not loaded. Try refreshing the page.');
  } finally {
    showLoading(false);
  }
}

async function highlightElements(tabId, selector) {
  showLoading(true);
  
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      action: 'HIGHLIGHT',
      selector
    });
    
    if (response.success) {
      showStatus(`Highlighted elements`, 'success');
    } else {
      showError(response.error);
    }
  } catch (error) {
    showError('Failed to highlight: ' + error.message);
  } finally {
    showLoading(false);
  }
}

async function injectScript(tabId) {
  showLoading(true);
  
  try {
    const response = await chrome.runtime.sendMessage({
      action: 'INJECT_SCRIPT',
      file: 'page-script.js'
    });
    
    if (response.success) {
      showStatus('Script injected', 'success');
    } else {
      showError(response.error);
    }
  } catch (error) {
    showError('Injection failed: ' + error.message);
  } finally {
    showLoading(false);
  }
}

function renderData(data) {
  const container = document.getElementById('results');
  
  container.innerHTML = `
    <div class="data-section">
      <h3>Page Info</h3>
      <p><strong>Title:</strong> ${escapeHtml(data.title)}</p>
      <p><strong>URL:</strong> ${escapeHtml(data.url)}</p>
    </div>
    
    <div class="data-section">
      <h3>Headings (${data.headings.length})</h3>
      <ul>
        ${data.headings.map(h => `
          <li><strong>${h.level}:</strong> ${escapeHtml(h.text)}</li>
        `).join('')}
      </ul>
    </div>
    
    <div class="data-section">
      <h3>Links (${data.links.length})</h3>
      <ul>
        ${data.links.map(l => `
          <li><a href="${l.href}" target="_blank">${escapeHtml(l.text || l.href)}</a></li>
        `).join('')}
      </ul>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showLoading(show) {
  document.getElementById('loading').classList.toggle('active', show);
}

function showStatus(message, type) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  
  setTimeout(() => {
    statusEl.className = 'status';
    statusEl.textContent = '';
  }, 3000);
}

function showError(message) {
  showStatus('Error: ' + message, 'error');
}
