const ALLOWED_ACTIONS = new Set(["navigate", "extract", "screenshot", "takeover_request", "release"]);

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "orville-relay-action") return false;
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
      const response = await fetch(`http://127.0.0.1:8787/api/v1/browser-relay/${encodeURIComponent(stored.relaySessionId)}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ secret: stored.relaySecret, action: message.action, payload: message.payload || {} })
      });
      const body = await response.json();
      sendResponse({ ok: response.ok, ...body });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
  });
  return true;
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url) return;
  const parsed = new URL(tab.url);
  if (!["http:", "https:"].includes(parsed.protocol)) return;
  await chrome.storage.session.set({ pairedTabId: tab.id, pairedOrigin: parsed.origin });
  await chrome.tabs.sendMessage(tab.id, { type: "orville-pair-ready", origin: parsed.origin }).catch(() => undefined);
});
