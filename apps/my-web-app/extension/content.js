/**
 * content.js
 *
 * Runs on chatgpt.com / chat.openai.com.
 *
 * Responsibilities:
 *   1. Shows a live token estimate next to the message composer (unchanged)
 *   2. Detects when a user sends a message and captures the input text
 *   3. Detects when an assistant response completes and captures the output
 *   4. Sends the exchange (input + output + tokens) to background.js for DB storage
 */

console.log("Sustainability tracker extension loaded");

// ─── Token estimator UI (unchanged from original) ────────────────────────────

let uiEl;
let boundEl;

function findComposer() {
  const pm = document.querySelector(
    '[contenteditable="true"][data-lexical-editor="true"], [contenteditable="true"].ProseMirror'
  );
  if (pm) return pm;

  const editables = [...document.querySelectorAll('[contenteditable="true"]')];
  const visible = editables.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 50 && r.height > 20 && r.bottom > window.innerHeight * 0.4;
  });
  if (visible.length) return visible[visible.length - 1];
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
  uiEl.style.cssText = "font-size:12px;opacity:0.75;margin-top:6px;padding-left:2px;";
  uiEl.textContent = "Estimated tokens: —";
  anchor.parentElement?.appendChild(uiEl);
  return uiEl;
}

function updateEstimate(el) {
  const text = getText(el);
  chrome.runtime.sendMessage({ type: "ESTIMATE_TOKENS", text }, (res) => {
    if (chrome.runtime.lastError) return;
    if (uiEl) uiEl.textContent = `Estimated tokens: ${res?.tokens ?? "—"}`;
  });
}

function attachTokenUI() {
  const composer = findComposer();
  if (!composer) return;
  ensureUI(composer);
  if (boundEl === composer) return;
  boundEl = composer;
  const handler = () => updateEstimate(composer);
  composer.addEventListener("input", handler);
  composer.addEventListener("keyup", handler);
  handler();
}

attachTokenUI();
new MutationObserver(() => attachTokenUI()).observe(document.documentElement, {
  childList: true,
  subtree: true,
});

// ─── Message capture ─────────────────────────────────────────────────────────

/** Snapshot of the last user input sent */
let pendingInput = null;

/** Count of assistant turns we have already recorded *for this URL* */
let recordedTurnCount = 0;

/** Last URL we tracked – used for SPA navigation detection */
let lastTrackedUrl = location.href;

function getMsgText(article) {
  const prose = article.querySelector(".markdown, [class*='prose']");
  if (prose) return prose.innerText.trim();
  return article.innerText.trim();
}

function getAllTurns() {
  return [
    ...document.querySelectorAll('article[data-testid^="conversation-turn-"]'),
  ];
}

function getAssistantTurns() {
  return getAllTurns().filter(
    (a) =>
      a.querySelector('[data-message-author-role="assistant"]') ||
      a.getAttribute("data-message-author-role") === "assistant"
  );
}

function getUserTurns() {
  return getAllTurns().filter(
    (a) =>
      a.querySelector('[data-message-author-role="user"]') ||
      a.getAttribute("data-message-author-role") === "user"
  );
}

function isStreaming() {
  return !!(
    document.querySelector('[data-testid="stop-button"]') ||
    document.querySelector('button[aria-label="Stop streaming"]') ||
    document.querySelector('button[aria-label="Stop generating"]')
  );
}

/** Reset all per-conversation counters */
function resetConversationState() {
  recordedTurnCount = 0;
  pendingInput = null;
  wasStreaming = false;
  console.log("[sustainability] conversation state reset for:", location.href);
}

/** Check for SPA URL change and reset if needed. Returns true if URL changed. */
function checkUrlChange() {
  if (location.href !== lastTrackedUrl) {
    lastTrackedUrl = location.href;
    resetConversationState();
    return true;
  }
  return false;
}

function captureExchange() {
  if (pendingInput === null) return;

  const assistantTurns = getAssistantTurns();
  const newTurns = assistantTurns.slice(recordedTurnCount);
  if (!newTurns.length) {
    console.log("[sustainability] captureExchange: no new assistant turns (recorded:", recordedTurnCount, "total:", assistantTurns.length, ")");
    return;
  }

  const lastTurn = newTurns[newTurns.length - 1];
  const outputText = getMsgText(lastTurn);

  if (!outputText) {
    console.log("[sustainability] captureExchange: empty output text, skipping");
    return;
  }

  const inputTokens = Math.max(1, pendingInput.split(/\s+/).length);
  const outputTokens = Math.max(1, outputText.split(/\s+/).length);

  const payload = {
    conversation_url: window.location.href,
    input_text: pendingInput,
    output_text: outputText,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
  };

  console.log("[sustainability] Recording message exchange:", payload);

  chrome.runtime.sendMessage({ type: "RECORD_MESSAGE", payload }, (res) => {
    if (chrome.runtime.lastError) {
      console.warn("[sustainability] RECORD_MESSAGE error:", chrome.runtime.lastError.message);
      return;
    }
    if (res?.ok) {
      recordedTurnCount = assistantTurns.length;
      console.log("[sustainability] Recorded message id:", res?.message?.id, "turnCount now:", recordedTurnCount);
    } else {
      console.warn("[sustainability] Failed to record message:", res?.error);
    }
  });

  pendingInput = null;
}

// ─── Streaming detection via MutationObserver ────────────────────────────────
let wasStreaming = false;

function captureInputText() {
  // Try composer first
  const composer = findComposer();
  const composerText = getText(composer).trim();
  if (composerText) {
    pendingInput = composerText;
    return;
  }
  // Composer already cleared – read the last user turn from the DOM
  const userTurns = getUserTurns();
  if (userTurns.length) {
    pendingInput = getMsgText(userTurns[userTurns.length - 1]);
  }
}

const streamObserver = new MutationObserver(() => {
  // Check for SPA navigation on every mutation
  checkUrlChange();

  const streaming = isStreaming();

  if (!wasStreaming && streaming) {
    captureInputText();
    wasStreaming = true;
    console.log("[sustainability] streaming started, pendingInput:", pendingInput?.substring(0, 60));
  } else if (wasStreaming && !streaming) {
    wasStreaming = false;
    console.log("[sustainability] streaming ended, will capture in 500ms");
    setTimeout(captureExchange, 500);
  }
});

streamObserver.observe(document.body, { childList: true, subtree: true });

// ─── Fallback: Periodic assistant-turn polling ──────────────────────────────
// In case streaming detection misses (e.g. after SPA navigation),
// poll every 2 s and record any unrecorded turns.
setInterval(() => {
  checkUrlChange();

  // Don't poll while streaming is active
  if (isStreaming()) return;

  const assistantTurns = getAssistantTurns();
  if (assistantTurns.length <= recordedTurnCount) return;

  // There are unrecorded assistant turns — try to pair with user input
  const userTurns = getUserTurns();

  // Walk through each unrecorded pair
  for (let i = recordedTurnCount; i < assistantTurns.length; i++) {
    const outputText = getMsgText(assistantTurns[i]);
    // The matching user turn is at the same index
    const inputText = i < userTurns.length ? getMsgText(userTurns[i]) : null;

    if (!outputText || !inputText) continue;

    const inputTokens = Math.max(1, inputText.split(/\s+/).length);
    const outputTokens = Math.max(1, outputText.split(/\s+/).length);

    const payload = {
      conversation_url: window.location.href,
      input_text: inputText,
      output_text: outputText,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    };

    console.log("[sustainability] Fallback recording turn", i, ":", payload.input_text.substring(0, 40));

    chrome.runtime.sendMessage({ type: "RECORD_MESSAGE", payload }, (res) => {
      if (chrome.runtime.lastError) {
        console.warn("[sustainability] Fallback RECORD_MESSAGE error:", chrome.runtime.lastError.message);
        return;
      }
      if (res?.ok) {
        console.log("[sustainability] Fallback recorded message id:", res?.message?.id);
      }
    });
  }

  // Mark all current turns as recorded
  recordedTurnCount = assistantTurns.length;
  pendingInput = null;
}, 2000);
