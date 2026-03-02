chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "ESTIMATE_TOKENS") {
    (async () => {
      try {
        const text = msg.text ?? "";
        const r = await fetch(
          `http://127.0.0.1:8001/estimate-tokens?text=${encodeURIComponent(text)}`,
        );
        const j = await r.json();
        sendResponse(j);
      } catch (e) {
        sendResponse({ error: String(e) });
      }
    })();
    return true; // IMPORTANT: keep sendResponse alive for async
  }

  if (msg?.type === "PING") sendResponse({ ok: true });
});

chrome.runtime.onInstalled.addListener(async () => {
  try {
    const r = await fetch("http://127.0.0.1:8001/health");
    const j = await r.json();
    console.log("dummy api health:", j);
  } catch (e) {
    console.error("dummy api fetch failed:", e);
  }
});
