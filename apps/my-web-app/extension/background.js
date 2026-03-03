/**
 * background.js  – Service Worker
 *
 * Responsibilities:
 *   1. Keycloak OIDC authentication (login / logout / token refresh)
 *   2. Record ChatGPT message exchanges to the backend API
 *   3. Token estimation proxy (unchanged from original)
 *   4. Expose auth state to popup via messages
 *
 * Keycloak config – keep in sync with the backend .env
 */

const KC_URL         = "http://localhost:8080";
const KC_REALM       = "sustainability";
const KC_CLIENT_ID   = "sustainability-extension";
const API_BASE       = "http://127.0.0.1:8787";

// The redirect URI Chrome provides for extensions using Identity API
// It will look like: https://<extension-id>.chromiumapp.org/
function getRedirectUri() {
  return chrome.identity.getRedirectURL();
}

// ─── Token storage helpers ────────────────────────────────────────────────────

async function saveTokens({ access_token, refresh_token, expires_in }) {
  const expires_at = Date.now() + (expires_in ?? 300) * 1000;
  await chrome.storage.local.set({ access_token, refresh_token, expires_at });
}

async function clearTokens() {
  await chrome.storage.local.remove(["access_token", "refresh_token", "expires_at"]);
}

async function getAccessToken() {
  const { access_token, refresh_token, expires_at } = await chrome.storage.local.get([
    "access_token",
    "refresh_token",
    "expires_at",
  ]);
  if (!access_token) return null;

  // Refresh if within 60 s of expiry
  if (Date.now() > (expires_at ?? 0) - 60_000) {
    if (!refresh_token) return null;
    return await refreshAccessToken(refresh_token);
  }
  return access_token;
}

async function refreshAccessToken(refresh_token) {
  try {
    const resp = await fetch(
      `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "refresh_token",
          client_id: KC_CLIENT_ID,
          refresh_token,
        }),
      }
    );
    if (!resp.ok) {
      await clearTokens();
      return null;
    }
    const data = await resp.json();
    await saveTokens(data);
    return data.access_token;
  } catch {
    await clearTokens();
    return null;
  }
}

// ─── Keycloak OIDC Login (Authorization Code + PKCE) ─────────────────────────

function base64url(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

async function generatePKCE() {
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const challenge = base64url(
    await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))
  );
  return { verifier, challenge };
}

async function login() {
  const { verifier, challenge } = await generatePKCE();
  const state = base64url(crypto.getRandomValues(new Uint8Array(16)));
  const redirectUri = getRedirectUri();

  // Persist verifier + state so we can exchange the code
  await chrome.storage.local.set({ pkce_verifier: verifier, oauth_state: state });

  const authUrl = new URL(
    `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/auth`
  );
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("client_id", KC_CLIENT_ID);
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("scope", "openid profile email");
  authUrl.searchParams.set("state", state);
  authUrl.searchParams.set("code_challenge", challenge);
  authUrl.searchParams.set("code_challenge_method", "S256");

  try {
    // Opens a pop-up window; resolves with the redirect URL containing ?code=…
    const resultUrl = await chrome.identity.launchWebAuthFlow({
      url: authUrl.toString(),
      interactive: true,
    });
    if (!resultUrl) throw new Error("Auth flow returned no URL");
    await exchangeCode(resultUrl, verifier, redirectUri);
    return { ok: true };
  } catch (err) {
    console.error("Login failed:", err);
    return { ok: false, error: String(err) };
  }
}

async function exchangeCode(resultUrl, verifier, redirectUri) {
  const url = new URL(resultUrl);
  const code = url.searchParams.get("code");
  if (!code) throw new Error("No code in redirect URL");

  const resp = await fetch(
    `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: KC_CLIENT_ID,
        redirect_uri: redirectUri,
        code,
        code_verifier: verifier,
      }),
    }
  );
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Token exchange failed: ${resp.status} – ${text}`);
  }
  const data = await resp.json();
  await saveTokens(data);
  await chrome.storage.local.remove(["pkce_verifier", "oauth_state"]);
}

async function logout() {
  const { refresh_token } = await chrome.storage.local.get("refresh_token");
  if (refresh_token) {
    // Ask Keycloak to revoke the session
    try {
      await fetch(
        `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/logout`,
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            client_id: KC_CLIENT_ID,
            refresh_token,
          }),
        }
      );
    } catch {
      // ignore – we clear locally regardless
    }
  }
  await clearTokens();
  return { ok: true };
}

// Decode the JWT payload (base64url) without signature verification
function decodeJwtPayload(token) {
  try {
    const [, payload] = token.split(".");
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

// ─── API helpers ─────────────────────────────────────────────────────────────

async function apiFetch(path, init = {}) {
  const token = await getAccessToken();
  if (!token) throw new Error("Not authenticated");
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`API ${path} → ${resp.status}: ${body}`);
  }
  return resp.json();
}

async function recordMessage(payload) {
  return apiFetch("/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchConversationMessages(url) {
  return apiFetch(`/conversations/messages?url=${encodeURIComponent(url)}`);
}

// ─── Token estimation (unchanged) ────────────────────────────────────────────

async function estimateTokens(text) {
  try {
    const r = await fetch(
      `${API_BASE}/estimate_tokens?text=${encodeURIComponent(text)}`
    );
    return r.json();
  } catch (e) {
    return { error: String(e) };
  }
}

// ─── Message listener ─────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    switch (msg?.type) {

      case "LOGIN":
        sendResponse(await login());
        break;

      case "STORE_TOKENS": {
        const { access_token, refresh_token, expires_in } = msg.tokens ?? {};
        if (access_token) await saveTokens({ access_token, refresh_token, expires_in });
        sendResponse({ ok: true });
        break;
      }

      case "LOGOUT":
        sendResponse(await logout());
        break;

      case "AUTH_STATE": {
        const token = await getAccessToken();
        if (!token) {
          sendResponse({ authenticated: false });
        } else {
          const payload = decodeJwtPayload(token);
          sendResponse({
            authenticated: true,
            name: payload?.name || payload?.preferred_username || "User",
            email: payload?.email,
          });
        }
        break;
      }

      case "RECORD_MESSAGE":
        try {
          const result = await recordMessage(msg.payload);
          sendResponse({ ok: true, message: result });
        } catch (err) {
          console.error("RECORD_MESSAGE failed:", err);
          sendResponse({ ok: false, error: String(err) });
        }
        break;

      case "FETCH_CONVERSATION":
        try {
          const messages = await fetchConversationMessages(msg.url);
          sendResponse({ ok: true, messages });
        } catch (err) {
          sendResponse({ ok: false, error: String(err) });
        }
        break;

      case "ESTIMATE_TOKENS":
        sendResponse(await estimateTokens(msg.text ?? ""));
        break;

      case "PING":
        sendResponse({ ok: true });
        break;

      default:
        sendResponse({ error: `Unknown message type: ${msg?.type}` });
    }
  })();
  return true; // keep sendResponse alive for async
});

// ─── On install – verify API health ──────────────────────────────────────────

chrome.runtime.onInstalled.addListener(async () => {
  try {
    const r = await fetch(`${API_BASE}/health`);
    const j = await r.json();
    console.log("API health:", j);
  } catch (e) {
    console.warn("API not reachable at install time:", e);
  }
});