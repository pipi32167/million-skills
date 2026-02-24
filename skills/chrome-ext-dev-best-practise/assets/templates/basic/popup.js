// Popup script
// Runs when user opens the extension popup

document.addEventListener('DOMContentLoaded', async () => {
  // Load initial data
  await loadData();
  
  // Set up event listeners
  document.getElementById('actionBtn').addEventListener('click', handleAction);
  document.getElementById('optionsBtn').addEventListener('click', openOptions);
});

async function loadData() {
  showLoading(true);
  
  try {
    // Get data from background script
    const response = await chrome.runtime.sendMessage({
      action: 'GET_DATA'
    });
    
    if (response.success) {
      renderData(response.data);
    } else {
      showError(response.error);
    }
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

async function handleAction() {
  showLoading(true);
  
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    const response = await chrome.runtime.sendMessage({
      action: 'SET_DATA',
      payload: { lastTab: tab.url }
    });
    
    if (response.success) {
      showStatus('Action completed!', 'success');
    } else {
      showError(response.error);
    }
  } catch (error) {
    showError(error.message);
  } finally {
    showLoading(false);
  }
}

function openOptions() {
  chrome.runtime.openOptionsPage();
}

function renderData(data) {
  // Render your data here
  console.log('Data:', data);
}

function showLoading(show) {
  document.getElementById('loading').classList.toggle('active', show);
}

function showStatus(message, type) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    statusEl.className = 'status';
    statusEl.textContent = '';
  }, 3000);
}

function showError(message) {
  showStatus(`Error: ${message}`, 'error');
}
