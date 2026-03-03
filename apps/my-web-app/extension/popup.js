/**
 * popup.js
 *
 * Handles:
 *   1. Auth state check + login/logout
 *   2. Fetching conversation messages from the API for the current tab URL
 *   3. Rendering messages as datapoints on the chart (total tokens per message)
 *   4. Point tooltip on hover/click
 */
(() => {
  // ─── Element refs ──────────────────────────────────────────────────────────
  const authSection   = document.getElementById('authSection');
  const mainPanel     = document.getElementById('mainPanel');
  const loginBtn      = document.getElementById('loginBtn');
  const logoutBtn     = document.getElementById('logoutBtn');
  const authStatusEl  = document.getElementById('authStatus');
  const userNameEl    = document.getElementById('userName');

  const statusEl      = document.getElementById('status');
  const metaEl        = document.getElementById('meta');
  const chipStatus    = document.getElementById('chipStatus');
  const refreshBtn    = document.getElementById('refreshBtn');

  const msgCountEl          = document.getElementById('msgCount');
  const totalInputTokensEl  = document.getElementById('totalInputTokens');
  const totalOutputTokensEl = document.getElementById('totalOutputTokens');
  const totalEnergyEl       = document.getElementById('totalEnergy');

  const canvas    = document.getElementById('chart');
  const ctx       = canvas.getContext('2d');

  // ─── Chart state ───────────────────────────────────────────────────────────
  let data      = [];   // array of message objects from API
  let pointsPx  = [];
  let DPR       = Math.max(1, window.devicePixelRatio || 1);
  const padding = { left: 18, right: 12, top: 14, bottom: 14 };

  // tooltip
  const tooltip = document.createElement('div');
  tooltip.className = 'chart-tooltip';
  tooltip.style.display = 'none';
  document.body.appendChild(tooltip);

  // ─── Logging helpers ───────────────────────────────────────────────────────
  function logStatus(msg, dim = false) {
    const line = document.createElement('div');
    line.className = 'console-line' + (dim ? ' dim' : '');
    line.textContent = `> ${msg}`;
    statusEl.prepend(line);
  }

  function clearStatus() {
    statusEl.innerHTML = '';
  }

  function logAuth(msg) {
    authStatusEl.style.display = '';
    const line = document.createElement('div');
    line.className = 'console-line';
    line.textContent = `> ${msg}`;
    authStatusEl.prepend(line);
  }

  function setChip(text) {
    chipStatus.textContent = text;
    chipStatus.className = 'status-badge mono';
    if (text === 'LOADED')          chipStatus.classList.add('status-loaded');
    else if (text === 'LOADING')    chipStatus.classList.add('status-importing');
    else if (text === 'SELECTED')   chipStatus.classList.add('status-selected');
  }

  // ─── Canvas helpers ────────────────────────────────────────────────────────
  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    // Don't set inline dimensions when panel is hidden (would override CSS width:100%)
    if (rect.width === 0 || rect.height === 0) return;
    canvas.width  = Math.round(rect.width  * DPR);
    canvas.height = Math.round(rect.height * DPR);
    canvas.style.width  = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }

  window.addEventListener('resize', () => {
    DPR = Math.max(1, window.devicePixelRatio || 1);
    resizeCanvas();
    render();
  });

  function xForIndex(i) {
    const w = canvas.getBoundingClientRect().width;
    const usable = w - padding.left - padding.right;
    if (data.length <= 1) return padding.left + usable / 2;
    return padding.left + i * (usable / (data.length - 1));
  }

  function yForValue(v, vmin, vmax) {
    const h = canvas.getBoundingClientRect().height;
    const usable = h - padding.top - padding.bottom;
    const t = (v - vmin) / Math.max(1e-8, vmax - vmin || 1);
    return padding.top + (1 - t) * usable;
  }

  function drawNoDataOverlay(rect) {
    ctx.save();
    ctx.font = '11px ui-monospace, monospace';
    ctx.fillStyle = '#666666';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('No messages recorded for this conversation', rect.width / 2, rect.height / 2 - 8);
    ctx.fillStyle = '#444444';
    ctx.font = '10px ui-monospace, monospace';
    ctx.fillText('Send a message in ChatGPT to start tracking', rect.width / 2, rect.height / 2 + 12);
    ctx.restore();
  }

  // ─── Stats UI ──────────────────────────────────────────────────────────────
  function updateStatsUI(msgs) {
    if (!msgs.length) {
      msgCountEl.textContent          = '—';
      totalInputTokensEl.textContent  = '—';
      totalOutputTokensEl.textContent = '—';
      totalEnergyEl.textContent       = '—';
      metaEl.textContent = 'No conversation data';
      return;
    }
    const totalIn  = msgs.reduce((s, m) => s + (m.input_tokens  || 0), 0);
    const totalOut = msgs.reduce((s, m) => s + (m.output_tokens || 0), 0);
    const totalE   = msgs.reduce((s, m) => s + (m.energy        || 0), 0);
    msgCountEl.textContent          = msgs.length;
    totalInputTokensEl.textContent  = totalIn;
    totalOutputTokensEl.textContent = totalOut;
    totalEnergyEl.textContent       = totalE.toFixed(2);
    metaEl.textContent = `${msgs.length} message${msgs.length !== 1 ? 's' : ''} in this conversation`;
  }

  // ─── Chart render ──────────────────────────────────────────────────────────
  /**
   * Each datapoint represents one recorded message.
   * Y-axis = estimated GPU energy in Joules for that message (from ML model).
   * Falls back to 0 if energy was not computed.
   */
  function render() {
    // Re-sync canvas buffer size every time we draw (handles display:none at init).
    resizeCanvas();
    const rect = canvas.getBoundingClientRect();
    console.log('[popup] render(): rect', rect.width, 'x', rect.height, 'data.length:', data.length);
    if (rect.width === 0 || rect.height === 0) return;
    ctx.clearRect(0, 0, rect.width, rect.height);

    ctx.save();
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, rect.width, rect.height);
    ctx.restore();

    if (!data.length) {
      drawNoDataOverlay(rect);
      return;
    }

    const values = data.map(m => m.energy != null ? m.energy : 0);
    const vmin = 0;
    const vmax = Math.max(...values, 1);

    pointsPx = data.map((m, i) => ({
      i,
      x: xForIndex(i),
      y: yForValue(values[i], vmin, vmax),
      d: m,
      v: values[i],
    }));

    // gridlines
    ctx.save();
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 1;
    for (let g = 0; g <= 3; g++) {
      const gy = padding.top + (g / 3) * (rect.height - padding.top - padding.bottom);
      ctx.beginPath();
      ctx.moveTo(padding.left, gy);
      ctx.lineTo(rect.width - padding.right, gy);
      ctx.stroke();
    }
    ctx.restore();

    // line
    ctx.save();
    ctx.beginPath();
    pointsPx.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#4a9eff';
    ctx.stroke();
    ctx.restore();

    // fill area
    ctx.save();
    ctx.beginPath();
    pointsPx.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.lineTo(rect.width - padding.right, rect.height - padding.bottom);
    ctx.lineTo(padding.left, rect.height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = 'rgba(74,158,255,0.08)';
    ctx.fill();
    ctx.restore();

    // dots
    pointsPx.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#4a9eff';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.strokeStyle = '#0a0a0a';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }

  // ─── Tooltip ───────────────────────────────────────────────────────────────
  function findNearestPoint(cssX, cssY, maxDist = 12) {
    if (!pointsPx.length) return null;
    let best = null, bestD = Infinity;
    for (const p of pointsPx) {
      const d = Math.hypot(p.x - cssX, p.y - cssY);
      if (d < bestD) { bestD = d; best = p; }
    }
    return bestD <= maxDist ? best : null;
  }

  function showTooltipForPoint(p, _clientX, _clientY) {
    if (!p) { tooltip.style.display = 'none'; return; }
    const m = p.d;
    const lines = [
      `msg #${p.i + 1}`,
      `energy: ${m.energy != null ? m.energy.toFixed(2) + ' J' : '—'}`,
      `tokens in: ${m.input_tokens ?? '—'}`,
      `tokens out: ${m.output_tokens ?? '—'}`,
    ];
    tooltip.innerHTML = lines.map(l => `<div>${l}</div>`).join('');
    tooltip.style.display = 'block';

    const pad = 8;
    const tr = tooltip.getBoundingClientRect();
    const cr = canvas.getBoundingClientRect();
    let left = cr.left + p.x;
    let top  = cr.top  + p.y;
    left = Math.max(pad + tr.width / 2, Math.min(window.innerWidth - pad - tr.width / 2, left));
    if (cr.top + p.y - tr.height - 18 < 0) {
      top += 18;
      tooltip.style.transform = 'translate(-50%, 0)';
    } else {
      top -= 12;
      tooltip.style.transform = 'translate(-50%, -120%)';
    }
    tooltip.style.left = `${left}px`;
    tooltip.style.top  = `${top}px`;
  }

  canvas.addEventListener('pointermove', (e) => {
    const r = canvas.getBoundingClientRect();
    const p = findNearestPoint(e.clientX - r.left, e.clientY - r.top, 10);
    p ? showTooltipForPoint(p) : (tooltip.style.display = 'none');
  });
  canvas.addEventListener('pointerleave', () => { tooltip.style.display = 'none'; });
  canvas.addEventListener('click', (e) => {
    const r  = canvas.getBoundingClientRect();
    const p  = findNearestPoint(e.clientX - r.left, e.clientY - r.top, 12);
    if (p) {
      showTooltipForPoint(p);
      setChip('SELECTED');
      logStatus(`msg #${p.i + 1} — ${p.v.toFixed(2)} J`);
    } else {
      tooltip.style.display = 'none';
      setChip('IDLE');
    }
  });

  // ─── Conversation data loading ─────────────────────────────────────────────
  async function loadConversationData() {
    clearStatus();
    setChip('LOADING');
    logStatus('fetching conversation data…', true);

    // Get the current tab URL
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab?.url;

    if (!url || (!url.includes('chatgpt.com') && !url.includes('chat.openai.com'))) {
      logStatus('Open a ChatGPT conversation to see data', true);
      setChip('IDLE');
      data = [];
      updateStatsUI([]);
      render();
      return;
    }

    chrome.runtime.sendMessage({ type: 'FETCH_CONVERSATION', url }, (res) => {
      if (chrome.runtime.lastError || !res?.ok) {
        logStatus(`Error: ${res?.error || chrome.runtime.lastError?.message}`, false);
        setChip('IDLE');
        return;
      }
      data = res.messages ?? [];
      console.log('[popup] Loaded', data.length, 'messages, first energy:', data[0]?.energy);
      updateStatsUI(data);
      setChip('LOADED');
      // Use rAF to ensure DOM has painted before measuring canvas
      requestAnimationFrame(() => render());
      logStatus(`Loaded ${data.length} message${data.length !== 1 ? 's' : ''}`, true);
    });
  }

  // ─── PKCE / Login helpers (run in popup context to avoid SW termination) ───
  function base64url(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)))
      .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  }

  async function generatePKCE() {
    const verifier  = base64url(crypto.getRandomValues(new Uint8Array(32)));
    const challenge = base64url(
      await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))
    );
    return { verifier, challenge };
  }

  async function exchangeCode(resultUrl, verifier, redirectUri) {
    const url  = new URL(resultUrl);
    const code = url.searchParams.get('code');
    if (!code) throw new Error('No code in redirect URL');
    const KC_URL      = 'http://localhost:8080';
    const KC_REALM    = 'sustainability';
    const KC_CLIENT_ID = 'sustainability-extension';
    const resp = await fetch(
      `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          grant_type:    'authorization_code',
          client_id:     KC_CLIENT_ID,
          redirect_uri:  redirectUri,
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
    // Persist tokens via background so the SW also has them
    await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: 'STORE_TOKENS', tokens: data }, (r) => {
        if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
        else resolve(r);
      });
    });
    return data;
  }

  async function login() {
    const KC_URL       = 'http://localhost:8080';
    const KC_REALM     = 'sustainability';
    const KC_CLIENT_ID = 'sustainability-extension';
    const { verifier, challenge } = await generatePKCE();
    const state       = base64url(crypto.getRandomValues(new Uint8Array(16)));
    const redirectUri = chrome.identity.getRedirectURL();

    const authUrl = new URL(`${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/auth`);
    authUrl.searchParams.set('response_type',          'code');
    authUrl.searchParams.set('client_id',              KC_CLIENT_ID);
    authUrl.searchParams.set('redirect_uri',           redirectUri);
    authUrl.searchParams.set('scope',                  'openid profile email');
    authUrl.searchParams.set('state',                  state);
    authUrl.searchParams.set('code_challenge',         challenge);
    authUrl.searchParams.set('code_challenge_method',  'S256');

    const resultUrl = await new Promise((resolve, reject) => {
      chrome.identity.launchWebAuthFlow(
        { url: authUrl.toString(), interactive: true },
        (url) => {
          if (chrome.runtime.lastError || !url) {
            reject(new Error(chrome.runtime.lastError?.message ?? 'Auth flow returned no URL'));
          } else {
            resolve(url);
          }
        }
      );
    });

    await exchangeCode(resultUrl, verifier, redirectUri);
    return { ok: true };
  }

  // ─── Auth flow ─────────────────────────────────────────────────────────────
  async function checkAuthAndInit() {
    chrome.runtime.sendMessage({ type: 'AUTH_STATE' }, (res) => {
      if (res?.authenticated) {
        showMainPanel(res.name);
        loadConversationData();
      } else {
        showAuthPanel();
      }
    });
  }

  function showAuthPanel() {
    authSection.style.display = '';
    mainPanel.style.display = 'none';
  }

  function showMainPanel(name) {
    authSection.style.display = 'none';
    mainPanel.style.display = '';
    userNameEl.textContent = name ?? '—';
    // Canvas now has real dimensions — force buffer sync
    requestAnimationFrame(() => { resizeCanvas(); render(); });
  }

  loginBtn.addEventListener('click', async () => {
    loginBtn.disabled = true;
    logAuth('Launching Keycloak login…');
    try {
      await login();
      chrome.runtime.sendMessage({ type: 'AUTH_STATE' }, (s) => {
        showMainPanel(s?.name);
        loadConversationData();
      });
    } catch (err) {
      logAuth(`Login failed: ${err.message ?? String(err)}`);
    } finally {
      loginBtn.disabled = false;
    }
  });

  logoutBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'LOGOUT' }, () => {
      data = [];
      showAuthPanel();
    });
  });

  refreshBtn.addEventListener('click', () => {
    loadConversationData();
  });

  // ─── Init ──────────────────────────────────────────────────────────────────
  DPR = Math.max(1, window.devicePixelRatio || 1);
  resizeCanvas();
  render();
  checkAuthAndInit();
})();