console.log("Token estimator extension loaded");

let uiEl;
let boundEl;
let debounceTimer = null;

// Find the *actual* message composer
function findComposer() {
  // Prefer ProseMirror (commonly used for the ChatGPT input)
  const pm = document.querySelector('[contenteditable="true"][data-lexical-editor="true"], [contenteditable="true"].ProseMirror');
  if (pm) return pm;

  // Fallback: first visible contenteditable near the bottom
  const editables = [...document.querySelectorAll('[contenteditable="true"]')];
  const visible = editables.filter(el => {
    const r = el.getBoundingClientRect();
    return r.width > 50 && r.height > 20 && r.bottom > window.innerHeight * 0.4;
  });
  if (visible.length) return visible[visible.length - 1];

  // Fallback: textarea (sometimes exists)
  return document.querySelector("textarea");
}

function getText(el) {
  if (!el) return "";
  if (el.tagName === "TEXTAREA") return el.value || "";
  // trim to avoid placeholder text counting as input
  return (el.textContent || "").trim();
}

function ensureUI(anchor) {
  // Always re-use the existing element if it's still in the DOM
  const existing = document.getElementById("token-estimator-ui");
  if (existing) {
    uiEl = existing;
    return uiEl;
  }

  uiEl = document.createElement("div");
  uiEl.id = "token-estimator-ui";
  uiEl.style.cssText = `
    font-size: 12px;
    opacity: 0.75;
    margin-top: 6px;
    padding-left: 2px;
  `;
  uiEl.textContent = "Estimated tokens: —";

  anchor.parentElement?.appendChild(uiEl);
  return uiEl;
}

function updateEstimate(el) {
  const text = getText(el);

  // If empty, show dashes immediately without hitting the API
  if (!text) {
    const target = document.getElementById("token-estimator-ui");
    if (target) target.textContent = "Estimated tokens: — · Est. GPU energy: —";
    return;
  }

  chrome.runtime.sendMessage({ type: "ESTIMATE_TOKENS", text }, (res) => {
    // Re-query by id so we always update the live element, not a stale reference
    const target = document.getElementById("token-estimator-ui");
    if (!target) return;

    if (chrome.runtime.lastError) {
      console.warn("sendMessage error:", chrome.runtime.lastError.message);
      target.textContent = "Estimated tokens: —";
      return;
    }
    const tokStr = res?.tokens != null ? res.tokens : "—";
    const energyStr = res?.power != null ? `${res.power.toFixed(4)} J` : "—";
    target.textContent = `Estimated tokens: ${tokStr} · Est. GPU energy: ${energyStr}`;
  });
}

function attach() {
  const composer = findComposer();
  if (!composer) return;

  ensureUI(composer);

  // Avoid double-binding if the DOM rerenders
  if (boundEl === composer) return;
  boundEl = composer;

  console.log("Bound to composer:", composer);

  // Debounce: wait 300 ms after the user stops typing before hitting the API
  const handler = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => updateEstimate(composer), 300);
  };

  composer.addEventListener("input", handler);
  // Trigger once on attach to set initial state
  updateEstimate(composer);
}

// Initial attach + reattach on rerenders
attach();
new MutationObserver(() => attach()).observe(document.documentElement, {
  childList: true,
  subtree: true
});
