const ALLOWED_ACTIONS = new Set(["navigate", "extract", "screenshot", "takeover_request", "release"]);

let relayConnection = null;
let config = { wsUrl: "ws://localhost:8766" };

chrome.storage.local.get(["relayConfig"], (result) => {
  if (result.relayConfig) {
    config = { ...config, ...result.relayConfig };
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message) {
    sendResponse({ ok: false, error: "empty-message" });
    return false;
  }
  if (message.type === "get-status") {
    chrome.storage.session.get(["relaySessionId", "relaySecret"], (stored) => {
      sendResponse({
        ok: true,
        connected: relayConnection !== null,
        paired: !!(stored.relaySessionId && stored.relaySecret),
        config: config
      });
    });
    return true;
  }
  if (message.type === "send-extracted" || message.type === "send-screenshot") {
    if (!relayConnection) {
      sendResponse({ ok: false, error: "not-connected" });
      return false;
    }
    try {
      relayConnection.send(JSON.stringify({
        type: message.type,
        timestamp: Date.now(),
        data: message.data
      }));
      sendResponse({ ok: true });
    } catch (err) {
      sendResponse({ ok: false, error: String(err) });
    }
    return false;
  }
  if (message.type === "send-checkin") {
    if (!relayConnection) {
      sendResponse({ ok: false, error: "not-connected" });
      return false;
    }
    try {
      relayConnection.send(JSON.stringify({
        type: "browser-checkin",
        timestamp: Date.now(),
        extension: true
      }));
      sendResponse({ ok: true });
    } catch (err) {
      sendResponse({ ok: false, error: String(err) });
    }
    return false;
  }
  if (message.type === "orville-relay-action") {
    return handleRelayAction(message, sender, sendResponse);
  }
  sendResponse({ ok: false, error: "unknown-message-type" });
  return false;
});

function handleRelayAction(message, sender, sendResponse) {
  if (!ALLOWED_ACTIONS.has(message.action)) {
    sendResponse({ ok: false, error: "action-not-allowlisted" });
    return false;
  }
  chrome.storage.session.get(["relaySessionId", "relaySecret"], async (stored) => {
    if (!stored.relaySessionId || !stored.relaySecret) {
      sendResponse({ ok: false, error: "extension-not-paired" });
      return;
    }
    try {
      const apiUrl = config.apiUrl || "http://127.0.0.1:8787";
      const response = await fetch(`${apiUrl}/api/v1/browser-relay/${encodeURIComponent(stored.relaySessionId)}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          secret: stored.relaySecret,
          action: message.action,
          payload: message.payload || {}
        })
      });
      const body = await response.json();
      sendResponse({ ok: response.ok, ...body });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
  });
  return true;
}

function connectToRelay() {
  try {
    relayConnection = new WebSocket(config.wsUrl);
    relayConnection.onopen = () => {
      relayConnection.send(JSON.stringify({
        type: "browser-connect",
        timestamp: Date.now(),
        version: chrome.runtime.getManifest().version
      }));
    };
    relayConnection.onclose = () => {
      relayConnection = null;
      setTimeout(connectToRelay, 3000);
    };
    relayConnection.onerror = () => {
      relayConnection = null;
    };
    relayConnection.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleRelayMessage(msg);
      } catch { }
    };
  } catch {
    relayConnection = null;
    setTimeout(connectToRelay, 3000);
  }
}

async function handleRelayMessage(msg) {
  if (!msg || !msg.action) return;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: "orville-bridge-action",
      action: msg.action,
      payload: msg.payload || {}
    });
    if (msg.requestId && relayConnection) {
      relayConnection.send(JSON.stringify({
        type: "action-response",
        requestId: msg.requestId,
        result: response
      }));
    }
  } catch { }
}

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url) return;
  const parsed = new URL(tab.url);
  if (!["http:", "https:"].includes(parsed.protocol)) return;
  await chrome.storage.session.set({ pairedTabId: tab.id, pairedOrigin: parsed.origin });
  await chrome.tabs.sendMessage(tab.id, { type: "orville-pair-ready", origin: parsed.origin }).catch(() => undefined);
});

chrome.runtime.onStartup.addListener(connectToRelay);
chrome.runtime.onInstalled.addListener(connectToRelay);
if (relayConnection === null) {
  connectToRelay();
}
