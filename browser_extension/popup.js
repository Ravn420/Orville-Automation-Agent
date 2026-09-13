/**
 * Orville Browser Operator - Popup Script
 * 
 * Handles the popup UI interactions and communicates with the background script.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  const btnExtract = document.getElementById('btn-extract');
  const btnScreenshot = document.getElementById('btn-screenshot');
  const btnCheckin = document.getElementById('btn-checkin');
  const relayUrl = document.getElementById('relay-url');
  const pageDomain = document.getElementById('page-domain');

  function updateStatus(state, message) {
    statusDot.className = 'status-dot ' + state;
    statusText.textContent = message;
    const connected = state === 'active';
    btnExtract.disabled = !connected;
    btnScreenshot.disabled = !connected;
    btnCheckin.disabled = false;
  }

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      pageDomain.textContent = new URL(tab.url).hostname || tab.url;
    }
  } catch {
    pageDomain.textContent = 'unknown';
  }

  try {
    const response = await chrome.runtime.sendMessage({ type: 'get-status' });
    if (response && response.ok) {
      updateStatus(response.connected ? 'active' : 'inactive', response.connected ? 'Connected to relay' : 'Not connected');
      if (response.config?.wsUrl) {
        relayUrl.textContent = response.config.wsUrl;
      }
    } else {
      updateStatus('inactive', 'Service not running');
    }
  } catch (err) {
    updateStatus('inactive', 'Error: ' + String(err).slice(0, 50));
  }

  btnExtract.addEventListener('click', async () => {
    try {
      btnExtract.disabled = true;
      btnExtract.textContent = 'Extracting...';
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const resp = await chrome.tabs.sendMessage(tab.id, {
        type: 'orville-bridge-action',
        action: 'extract',
        payload: { mode: 'structured' }
      });
      if (resp && resp.ok) {
        await chrome.runtime.sendMessage({
          type: 'send-extracted',
          data: resp.result
        });
        btnExtract.textContent = 'Extracted! Sent to relay';
      } else {
        btnExtract.textContent = 'Failed: ' + (resp?.error || 'unknown');
      }
    } catch (err) {
      btnExtract.textContent = 'Error: ' + String(err).slice(0, 30);
    }
    setTimeout(() => {
      btnExtract.disabled = false;
      btnExtract.textContent = 'Extract Page Data';
    }, 2000);
  });

  btnScreenshot.addEventListener('click', async () => {
    try {
      btnScreenshot.disabled = true;
      btnScreenshot.textContent = 'Capturing...';
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const resp = await chrome.tabs.sendMessage(tab.id, {
        type: 'orville-bridge-action',
        action: 'screenshot',
        payload: {}
      });
      if (resp && resp.ok) {
        await chrome.runtime.sendMessage({
          type: 'send-screenshot',
          data: resp.result
        });
        btnScreenshot.textContent = 'Captured! Sent to relay';
      } else {
        btnScreenshot.textContent = 'Failed: ' + (resp?.error || 'unknown');
      }
    } catch (err) {
      btnScreenshot.textContent = 'Error: ' + String(err).slice(0, 30);
    }
    setTimeout(() => {
      btnScreenshot.disabled = false;
      btnScreenshot.textContent = 'Capture Screenshot';
    }, 2000);
  });

  btnCheckin.addEventListener('click', async () => {
    try {
      btnCheckin.textContent = 'Checking in...';
      await chrome.runtime.sendMessage({ type: 'send-checkin' });
      btnCheckin.textContent = 'Checked in!';
    } catch (err) {
      btnCheckin.textContent = 'Error: ' + String(err).slice(0, 30);
    }
    setTimeout(() => {
      btnCheckin.textContent = 'Check in Agent';
    }, 2000);
  });
});
