chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "ESTIMATE_TOKENS") {
    sendResponse({ tokens: 123 });
  }
  if (msg?.type === "PING") sendResponse({ ok: true });
});
