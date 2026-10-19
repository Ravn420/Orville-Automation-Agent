/**
 * Orville Browser Operator - Content Script
 * 
 * Injected into web pages to enable DOM extraction and page interaction
 * via the configured browser relay.
 */

(function () {
  'use strict';

  const ALLOWED_ACTIONS = new Set(["navigate", "extract", "screenshot", "takeover_request", "release"]);
  const ALLOWED_SELECTORS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a[href]', 'button', 'input', 'form', 'article', 'main', '[role="main"]'];
  const MAX_TEXT_LENGTH = 500;

  function extractText(node) {
    if (!node) return '';
    if (node.nodeType === Node.TEXT_NODE) {
      return node.textContent?.trim() || '';
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return '';
    return node.innerText?.trim() || node.textContent?.trim() || '';
  }

  function computeImportance(element) {
    const tag = element.tagName?.toLowerCase() || '';
    const isHeading = /^h[1-6]$/.test(tag);
    const textLen = extractText(element).length;
    let score = 0;
    if (isHeading) score += 10 - parseInt(tag[1] || '0');
    if (tag === 'article') score += 5;
    if (element.id === 'main' || element.getAttribute('role') === 'main') score += 8;
    score += Math.min(3, textLen / 1000);
    return score;
  }

  function extractStructured() {
    const elements = Array.from(document.querySelectorAll(ALLOWED_SELECTORS.join(',')));
    const seen = new Set();
    const items = [];
    for (const el of elements) {
      if (seen.has(el)) continue;
      const text = extractText(el);
      if (!text || text.length < 3) continue;
      seen.add(el);
      const rect = el.getBoundingClientRect?.();
      const item = {
        tag: el.tagName?.toLowerCase(),
        text: text.slice(0, MAX_TEXT_LENGTH),
        href: el.href || el.action || undefined,
        importance: computeImportance(el),
        id: el.id || undefined,
        classes: el.className?.split?.(/\s+/)?.filter(Boolean)?.slice(0, 3) || undefined,
        position: rect ? { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) } : undefined
      };
      items.push(item);
    }
    items.sort((a, b) => b.importance - a.importance);
    return {
      title: document.title || '',
      url: location.href,
      timestamp: new Date().toISOString(),
      elements: items.slice(0, 100)
    };
  }

  function extractNavigation() {
    const links = Array.from(document.querySelectorAll('a[href]'));
    return {
      links: links
        .filter(a => a.href && new URL(a.href).origin === location.origin)
        .map(a => ({ text: extractText(a).slice(0, MAX_TEXT_LENGTH), href: a.href }))
        .slice(0, 50)
    };
  }

  function extractForms() {
    const forms = Array.from(document.querySelectorAll('form'));
    return {
      forms: forms.map(f => ({
        id: f.id || undefined,
        action: f.action || undefined,
        method: f.method || 'get',
        fields: Array.from(f.elements)
          .filter(e => e.name)
          .map(e => ({
            name: e.name,
            type: e.type || e.tagName?.toLowerCase(),
            required: e.required || false,
            placeholder: e.placeholder || undefined
          }))
      }))
    };
  }

  function handleExtract(payload) {
    const mode = payload?.mode || 'structured';
    switch (mode) {
      case 'navigation':
        return extractNavigation();
      case 'forms':
        return extractForms();
      case 'full':
        return { text: document.body?.innerText?.slice(0, 100000) || '' };
      case 'structured':
      default:
        return extractStructured();
    }
  }

  function handleNavigate(payload) {
    const url = payload?.url;
    if (!url) throw new Error('navigate requires "url"');
    let target;
    try {
      target = new URL(url, location.href).href;
    } catch {
      throw new Error('invalid url: ' + url);
    }
    location.assign(target);
    return { navigated: true, to: target };
  }

  async function takeScreenshot() {
    try {
      if (document.documentElement && document.documentElement.scrollHeight && document.documentElement.scrollWidth) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = document.documentElement.scrollWidth;
        canvas.height = Math.min(10000, document.documentElement.scrollHeight);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/png');
        return { dataUrl: dataUrl.slice(0, 100) + '...', length: dataUrl.length, mimeType: 'image/png' };
      }
    } catch (e) {
    }
    throw new Error('content-screenshot-fallback: use relay viewport capture');
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || message.type !== 'orville-bridge-action') {
      return false;
    }
    if (!message.action || !ALLOWED_ACTIONS.has(message.action)) {
      sendResponse({ ok: false, error: 'action-not-allowed' });
      return false;
    }
    (async () => {
      try {
        let result;
        switch (message.action) {
          case 'navigate':
            result = handleNavigate(message.payload);
            break;
          case 'extract':
            result = handleExtract(message.payload);
            break;
          case 'screenshot':
            result = await takeScreenshot();
            break;
          case 'takeover_request':
            result = { acknowledged: true };
            break;
          case 'release':
            result = { released: true };
            break;
          default:
            throw new Error('unknown action: ' + message.action);
        }
        sendResponse({ ok: true, result });
      } catch (err) {
        sendResponse({ ok: false, error: String(err) });
      }
    })();
    return true;
  });

})();
