// popup.js
(() => {
  const fileInput = document.getElementById('file');
  const resetBtn = document.getElementById('reset');
  const statusEl = document.getElementById('status');
  const metaEl = document.getElementById('meta');
  const chipStatus = document.getElementById('chipStatus');

  const avgUtilEl = document.getElementById('avgUtil');
  const maxUtilEl = document.getElementById('maxUtil');
  const maxMemEl = document.getElementById('maxMem');
  const pointsEl = document.getElementById('points');

  const canvas = document.getElementById('chart');
  const container = canvas.closest('.chart-container');
  const ctx = canvas.getContext('2d');

  // tooltip element (created dynamically)
  const tooltip = document.createElement('div');
  tooltip.className = 'chart-tooltip';
  tooltip.style.display = 'none';
  document.body.appendChild(tooltip);

  // keep data & layout state
  let data = []; // array of {util, mem?, ts?}
  let pointsPx = []; // precomputed canvas pixel coords for each point
  let DPR = Math.max(1, window.devicePixelRatio || 1);
  const padding = { left: 18, right: 12, top: 14, bottom: 14 };

  function logStatus(msg, dim = false) {
    const line = document.createElement('div');
    line.className = 'console-line' + (dim ? ' dim' : '');
    line.textContent = `> ${msg}`;
    statusEl.prepend(line);
  }

  function clearStatus() {
    statusEl.innerHTML = '';
  }

  function setChip(text) {
    chipStatus.textContent = text;
    // Update class for styling
    chipStatus.className = 'status-badge mono';
    if (text === 'LOADED') {
      chipStatus.classList.add('status-loaded');
    } else if (text === 'IMPORTING') {
      chipStatus.classList.add('status-importing');
    } else if (text === 'POINT SELECTED') {
      chipStatus.classList.add('status-selected');
    }
  }

  // resize canvas for DPR
  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.round(rect.width * DPR);
    canvas.height = Math.round(rect.height * DPR);
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0); // work in CSS pixels
  }

  window.addEventListener('resize', () => {
    DPR = Math.max(1, window.devicePixelRatio || 1);
    resizeCanvas();
    render();
  });

  // utility mapping functions
  function xForIndex(i) {
    const w = canvas.getBoundingClientRect().width;
    const usable = w - padding.left - padding.right;
    if (data.length <= 1) return padding.left + usable / 2;
    const step = usable / (data.length - 1);
    return padding.left + i * step;
  }

  function yForValue(v, min, max) {
    const h = canvas.getBoundingClientRect().height;
    const usable = h - padding.top - padding.bottom;
    // invert Y: higher util -> closer to top
    const t = (v - min) / Math.max(1e-8, (max - min || 1));
    return padding.top + (1 - t) * usable;
  }

  function computeStats(rows) {
    if (!rows.length) return { avg: 0, maxU: 0, maxM: 0 };
    const utils = rows.map(r => Number(r.util) || 0);
    const mems = rows.map(r => Number(r.mem) || 0);
    const avg = utils.reduce((a, b) => a + b, 0) / utils.length;
    const maxU = Math.max(...utils);
    const maxM = mems.length ? Math.max(...mems) : 0;
    return { avg, maxU, maxM };
  }

  function updateStatsUI(rows) {
    const { avg, maxU, maxM } = computeStats(rows);
    avgUtilEl.textContent = rows.length ? `${Math.round(avg)}` : '—';
    maxUtilEl.textContent = rows.length ? `${Math.round(maxU)}` : '—';
    maxMemEl.textContent = rows.length ? `${Math.round(maxM)}` : '—';
    pointsEl.textContent = rows.length || '—';
    metaEl.textContent = rows.length ? `${fileInput.files?.length ? 'datagen_output' : 'dataset'} • ${rows.length} points` : 'Loading dataset...';
  }

  // draw rounded rect helper
  function roundRect(ctx, x, y, w, h, r = 8) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // main render
  function render() {
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    // clear
    ctx.clearRect(0, 0, rect.width, rect.height);

    // compute min/max (with small padding)
    if (!data.length) {
      // empty placeholder
      drawNoDataOverlay(ctx, rect);
      return;
    }

    const utils = data.map(d => Number(d.util) || 0);
    const min = Math.min(...utils, 0);
    const max = Math.max(...utils, 100);
    const rangeMargin = Math.max(1, (max - min) * 0.06);
    const vmin = Math.max(0, min - rangeMargin);
    const vmax = Math.min(100, max + rangeMargin);

    // background panel
    ctx.save();
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, rect.width, rect.height);
    ctx.restore();

    // create points px cache
    pointsPx = data.map((d, i) => {
      return {
        i,
        x: xForIndex(i),
        y: yForValue(Number(d.util) || 0, vmin, vmax),
        d
      };
    });

    // draw gridlines (subtle terminal style)
    ctx.save();
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 1;
    const gridYCount = 3;
    for (let g = 0; g <= gridYCount; g++) {
      const gy = padding.top + (g / gridYCount) * (rect.height - padding.top - padding.bottom);
      ctx.beginPath();
      ctx.moveTo(padding.left, gy);
      ctx.lineTo(rect.width - padding.right, gy);
      ctx.stroke();
    }
    ctx.restore();

    // draw line
    ctx.save();
    ctx.beginPath();
    pointsPx.forEach((p, idx) => {
      if (idx === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    // accent color for line
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#4a9eff';
    ctx.stroke();
    ctx.restore();

    // draw area under line (subtle)
    ctx.save();
    ctx.beginPath();
    pointsPx.forEach((p, idx) => {
      if (idx === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    });
    ctx.lineTo(rect.width - padding.right, rect.height - padding.bottom);
    ctx.lineTo(padding.left, rect.height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = 'rgba(74, 158, 255, 0.08)';
    ctx.fill();
    ctx.restore();

    // draw points
    pointsPx.forEach(p => {
      // point
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#4a9eff';
      ctx.fill();

      // stroke
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.strokeStyle = '#0a0a0a';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }

  // find nearest point within threshold (in CSS pixels)
  function findNearestPoint(cssX, cssY, maxDist = 12) {
    if (!pointsPx.length) return null;
    let best = null;
    let bestD = Infinity;
    for (const p of pointsPx) {
      const dx = p.x - cssX;
      const dy = p.y - cssY;
      const d = Math.hypot(dx, dy);
      if (d < bestD) {
        bestD = d;
        best = p;
      }
    }
    return bestD <= maxDist ? best : null;
  }

  // show tooltip for a point (positions it)
  function showTooltipForPoint(p, clientX, clientY) {
    if (!p) {
      tooltip.style.display = 'none';
      return;
    }
    const d = p.d;
    const lines = [];
    if (d.ts !== undefined) lines.push(`ts: ${d.ts}`);
    lines.push(`util: ${d.util}%`);
    if (d.mem !== undefined) lines.push(`mem: ${d.mem}`);
    tooltip.innerHTML = lines.map(l => `<div>${l}</div>`).join('');
    tooltip.style.display = 'block';

    // position near the click, but keep inside viewport
    const pad = 8;
    const tooltipRect = tooltip.getBoundingClientRect();
    // prefer above the point; compute canvas rect + p.x/p.y
    const canvasRect = canvas.getBoundingClientRect();
    const absoluteX = canvasRect.left + p.x;
    const absoluteY = canvasRect.top + p.y;

    // default: above
    let left = absoluteX;
    let top = absoluteY - 12;

    // avoid clipping left/right
    left = Math.max(pad + tooltipRect.width / 2, Math.min(window.innerWidth - pad - tooltipRect.width / 2, left));
    // if not much room above, put below
    if (absoluteY - tooltipRect.height - 18 < 0) {
      top = absoluteY + 18;
      tooltip.style.transform = 'translate(-50%, 0)';
    } else {
      tooltip.style.transform = 'translate(-50%, -120%)';
    }

    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  // click / hover handlers
  function onCanvasPointerMove(e) {
    const rect = canvas.getBoundingClientRect();
    const cssX = e.clientX - rect.left;
    const cssY = e.clientY - rect.top;
    const nearest = findNearestPoint(cssX, cssY, 10);
    if (nearest) {
      // show small hover tooltip
      showTooltipForPoint(nearest, e.clientX, e.clientY);
    } else {
      tooltip.style.display = 'none';
    }
  }

  function onCanvasClick(e) {
    const rect = canvas.getBoundingClientRect();
    const cssX = e.clientX - rect.left;
    const cssY = e.clientY - rect.top;
    const nearest = findNearestPoint(cssX, cssY, 12);
    if (nearest) {
      // toggle persistent tooltip (click keeps visible)
      showTooltipForPoint(nearest, e.clientX, e.clientY);
      setChip('POINT SELECTED');
      logStatus(`selected point index ${nearest.i} util=${nearest.d.util}`, false);
    } else {
      tooltip.style.display = 'none';
      setChip('IDLE');
    }
  }

  // file parsing -> load into data and render
  function handleFileLoadText(text) {
    clearStatus();
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (err) {
      logStatus('Invalid JSON', false);
      console.error(err);
      return;
    }

    // allow the JSON to be either an object with a property (datagen output), or a direct array
    if (Array.isArray(parsed)) {
      data = parsed.map(normalizeRow);
    } else if (Array.isArray(parsed.data)) {
      data = parsed.data.map(normalizeRow);
    } else {
      // fallback: try to find the first array inside the object
      const arr = Object.values(parsed).find(v => Array.isArray(v));
      if (arr) data = arr.map(normalizeRow);
      else {
        logStatus('No array of rows found in JSON', false);
        return;
      }
    }

    updateStatsUI(data);
    setChip('LOADED');
    render();
    logStatus(`Loaded ${data.length} rows`);
  }

  // ---- Replace normalizeRow(), handleFileLoadText() and add drawNoDataOverlay() ----

function normalizeRow(r) {
  // Try to extract a util-like value from many possible field names
  const candidate =
    r?.util ??
    r?.util_percent ??
    r?.util_pct ??
    r?.u ??
    r?.usage ??
    r?.gpu_util ??
    r?.gpu_gpu_util_avg ??  // datagen_output.json format
    r?.gpu_gpu_util_max ??  // datagen_output.json format (fallback)
    r?.value ??
    r?.[0] ??
    r?.percentage ??
    undefined;

  // coerce to a number, handle "50%" or "50.0" or "0.5"
  if (candidate === undefined || candidate === null) {
    return {
      util: NaN,
      mem: (r?.mem ?? r?.memory ?? r?.m ?? undefined),
      ts: (r?.ts ?? r?.timestamp ?? r?.time ?? undefined),
      raw: r
    };
  }

  let utilNum;
  if (typeof candidate === 'number') {
    utilNum = candidate;
  } else {
    const s = String(candidate).trim();
    // If contains %, strip it
    if (s.endsWith('%')) {
      utilNum = Number(s.replace('%','').trim());
    } else {
      // parse float
      const parsed = Number(s);
      if (!Number.isNaN(parsed)) {
        utilNum = parsed;
      } else {
        // try parse as fraction (0-1 -> 0-100)
        const maybe = parseFloat(s);
        if (!Number.isNaN(maybe) && Math.abs(maybe) <= 1) utilNum = maybe * 100;
        else utilNum = NaN;
      }
    }
  }

  // normalize mem similarly but keep optional
  let memVal;
  const memCandidate = 
    r?.mem ?? 
    r?.memory ?? 
    r?.mem_percent ?? 
    r?.gpu_memory_avg_mib ??  // datagen_output.json format
    r?.gpu_memory_max_mib ??  // datagen_output.json format (fallback)
    r?.m ?? 
    undefined;
  if (memCandidate === undefined || memCandidate === null) memVal = undefined;
  else {
    const ms = String(memCandidate).trim();
    memVal = ms.endsWith('%') ? Number(ms.replace('%','').trim()) : Number(ms);
    if (Number.isNaN(memVal)) memVal = undefined;
  }

  return {
    util: utilNum,
    mem: memVal,
    ts: (r?.ts ?? r?.timestamp ?? r?.time ?? undefined),
    raw: r
  };
}

function drawNoDataOverlay(ctx, rect) {
  // draw a faint message in the chart area to indicate why nothing plotted
  ctx.save();
  ctx.font = '11px ui-monospace, monospace';
  ctx.fillStyle = '#666666';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('No numeric "util" values found in dataset', rect.width / 2, rect.height / 2 - 8);
  ctx.fillStyle = '#444444';
  ctx.font = '10px ui-monospace, monospace';
  ctx.fillText('Check console for parsed JSON sample', rect.width / 2, rect.height / 2 + 12);
  ctx.restore();
}

function handleFileLoadText(text) {
  clearStatus();
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    logStatus('Invalid JSON', false);
    console.error('JSON parse failed', err);
    return;
  }

  // DEBUG: show the raw parsed top-level shape so you can inspect in console
  console.groupCollapsed('Loaded JSON sample');
  console.log(parsed);
  // log a compact preview (first 3 items if array)
  if (Array.isArray(parsed)) {
    console.log('Top-level is array, first items:', parsed.slice(0,3));
  } else if (Array.isArray(parsed?.data)) {
    console.log('Top-level has .data array, first items:', parsed.data.slice(0,3));
  } else {
    // show keys and first array found
    console.log('Top-level keys:', Object.keys(parsed));
    const arr = Object.values(parsed).find(v => Array.isArray(v));
    if (arr) console.log('Found array at property; first items:', arr.slice(0,3));
  }
  console.groupEnd();

  // locate array of rows
  let arr;
  if (Array.isArray(parsed)) arr = parsed;
  else if (Array.isArray(parsed.data)) arr = parsed.data;
  else arr = Object.values(parsed).find(v => Array.isArray(v));

  if (!arr || !Array.isArray(arr)) {
    logStatus('No array of rows found in JSON (check console)', false);
    console.error('No array of rows found — parsed top-level object is:', parsed);
    return;
  }

  // normalize and coerce
  data = arr.map(normalizeRow);

  // quick diagnostics: count numeric utils
  const numericCount = data.reduce((c, r) => c + (Number.isFinite(r.util) ? 1 : 0), 0);
  console.log(`Normalized rows: ${data.length} (numeric util: ${numericCount})`);
  if (numericCount === 0) {
    logStatus('Loaded file but found 0 numeric util values — check field names or formats', false);
    setChip('LOADED (no util)');
    // still update UI and render a visible overlay
    updateStatsUI([]);
    // ensure canvas will show overlay: call render which will use drawNoDataOverlay
    render();
    return;
  }

  updateStatsUI(data);
  setChip('LOADED');
  render();
  logStatus(`Loaded ${data.length} rows (${numericCount} numeric util)`);
}


  // wire file input
  fileInput.addEventListener('change', (ev) => {
    const f = ev.target.files && ev.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = (e) => handleFileLoadText(e.target.result);
    reader.onerror = () => logStatus('Error reading file', false);
    reader.readAsText(f);
    setChip('IMPORTING');
    logStatus(`reading ${f.name}`);
  });

  resetBtn.addEventListener('click', () => {
    data = [];
    updateStatsUI([]);
    clearStatus();
    setChip('IDLE');
    tooltip.style.display = 'none';
    render();
  });

  // interactions
  canvas.addEventListener('pointermove', onCanvasPointerMove);
  canvas.addEventListener('pointerleave', () => { tooltip.style.display = 'none'; });
  canvas.addEventListener('click', onCanvasClick);

  // Auto-load default dataset on startup
  async function loadDefaultDataset() {
    try {
      const response = await fetch(chrome.runtime.getURL('data/datagen_output.json'));
      if (!response.ok) {
        throw new Error(`Failed to load default dataset: ${response.statusText}`);
      }
      const text = await response.text();
      handleFileLoadText(text);
      logStatus('Loaded default dataset: datagen_output.json', true);
    } catch (error) {
      console.warn('Could not load default dataset:', error);
      logStatus('Default dataset not available', true);
    }
  }

  // initial setup
  DPR = Math.max(1, window.devicePixelRatio || 1);
  resizeCanvas();
  render();

  // Load default dataset automatically
  loadDefaultDataset();

  // expose render for debugging (optional)
  window.__gpuUtil = { render, data, showTooltipForPoint };
})();
