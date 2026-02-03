console.log("Token estimator extension loaded");

let uiEl;
let boundEl;

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
  return el.textContent || "";
}

function ensureUI(anchor) {
  if (uiEl && document.contains(uiEl)) return uiEl;

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

  chrome.runtime.sendMessage({ type: "ESTIMATE_TOKENS", text }, (res) => {
    if (chrome.runtime.lastError) {
      console.warn("sendMessage error:", chrome.runtime.lastError.message);
      uiEl.textContent = "Estimated tokens: —";
      return;
    }
    uiEl.textContent = `Estimated tokens: ${res?.tokens ?? "—"}`;
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

  const handler = () => updateEstimate(composer);

  composer.addEventListener("input", handler);
  composer.addEventListener("keyup", handler); // extra reliability
  handler();
}

// Initial attach + reattach on rerenders
attach();
new MutationObserver(() => attach()).observe(document.documentElement, {
  childList: true,
  subtree: true
});
