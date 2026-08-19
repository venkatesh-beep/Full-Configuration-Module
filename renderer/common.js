/* =========================================================
 * common.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Owns: shared runtime state + generic utility helpers used by
 *       every module (API headers, Excel I/O, parsing, DOM helpers).
 * Load order requirement: loads AFTER styles.js, BEFORE router/audit/
 * notifications/login. Because of that, this file must NOT read
 * AppCtx.Audit / AppCtx.Notifications at the top level — only lazily,
 * inside function bodies, at the moment they're actually called
 * (by which time the full app has finished bootstrapping).
 * ========================================================= */
'use strict';
// ---------------------------------------------------------
// Constants
// ---------------------------------------------------------
var BASIC_AUTH = 'Basic YWRtaW4tY2xpZW50Oms0UCFYUmZRS3hEUyRtQHc=';
var TOKEN_VALIDITY_MIN = 120;

// ---------------------------------------------------------
// Environments — 2 tenants × 2 stages = 4 URLs total.
// Nested as ENVIRONMENTS[tenantKey][stageKey] = { label, url }.
// tenant-level `label`/`icon` are used by renderEnvSelector().
// ---------------------------------------------------------
var ENVIRONMENTS = {
  esampark: {
    label: 'eSampark (Flipkart)',
    icon: '🛒',
    production: { label: 'Production', url: 'https://esampark.beeforce.in' },
    uat:        { label: 'UAT',        url: 'https://esampark-uat.beeforce.in' }
  },
  beeforce: {
    label: 'BeeForce',
    icon: '🐝',
    production: { label: 'Production', url: 'https://app.beeforce.in' },
    uat:        { label: 'UAT',        url: 'https://app-uat.beeforce.in' }
  }
};

// ---------------------------------------------------------
// Global, mutable application state
// (was scattered across window.BF_* globals + a bare `cache` object
// in the legacy monolith — now lives on AppCtx.AppState)
// ---------------------------------------------------------
var AppState = {
  BASE_URL: ENVIRONMENTS.esampark.production.url, // preserves old default
  TENANT: 'esampark',
  ENV: 'production',
  TOKEN: null,
  TOKEN_ISSUED: 0,
  USERNAME: null,
  cache: {} // per-module scratch storage, keyed like cache.pe, cache.tc, etc.
};

// ---------------------------------------------------------
// Environment selection
// ---------------------------------------------------------
/**
 * setEnvironment(tenantKey, stageKey) — updates AppState.TENANT/ENV/BASE_URL.
 * Returns the resolved URL, or null if the combination doesn't exist.
 */
function setEnvironment(tenantKey, stageKey) {
  var tenant = ENVIRONMENTS[tenantKey];
  var stage = tenant && tenant[stageKey];
  if (!stage) return null;
  AppState.TENANT = tenantKey;
  AppState.ENV = stageKey;
  AppState.BASE_URL = stage.url;
  return AppState.BASE_URL;
}

function getEnvironmentUrl(tenantKey, stageKey) {
  var tenant = ENVIRONMENTS[tenantKey];
  var stage = tenant && tenant[stageKey];
  return stage ? stage.url : null;
}

function injectEnvSelectorStyles() {
  if (document.getElementById('bf-env-selector-styles')) return;
  var style = document.createElement('style');
  style.id = 'bf-env-selector-styles';
  style.textContent =
    '.bf-env-selector{display:flex;flex-direction:column;gap:8px;width:100%;margin-bottom:6px;}' +
    '.bf-env-row{display:flex;align-items:center;gap:10px;}' +
    '.bf-env-row-label{font-size:10.5px;font-weight:700;letter-spacing:.05em;color:#94a3b8;width:46px;flex-shrink:0;text-transform:uppercase;}' +
    '.bf-env-pills{display:flex;gap:4px;flex:1;background:#f1f5f9;padding:3px;border-radius:9px;}' +
    '.bf-env-pill{flex:1;border:none;background:transparent;padding:7px 8px;border-radius:7px;font-size:12.5px;font-weight:600;color:#64748b;cursor:pointer;transition:background .12s ease,color .12s ease,box-shadow .12s ease;font-family:inherit;white-space:nowrap;}' +
    '.bf-env-pill:hover{color:#1e293b;}' +
    '.bf-env-pill.active{background:#ffffff;color:#0f172a;box-shadow:0 1px 3px rgba(15,23,42,.16);}' +
    '.bf-env-pill-prod.active{color:#15803d;}' +
    '.bf-env-pill-uat.active{color:#c2410c;}' +
    '.bf-env-preview{font-size:11px;color:#94a3b8;text-align:right;padding-right:2px;}' +
    '.bf-env-preview b{font-weight:600;color:#1D4ED8;}';
  document.head.appendChild(style);
}

/**
 * renderEnvSelector(container, opts) — draws a compact two-row segmented
 * picker (Tenant pills, Stage pills) into `container` (a DOM element or
 * element id) and wires clicks to setEnvironment(). Call this from
 * login.js before/at the login screen.
 *
 * opts.onSelect(tenantKey, stageKey, url) — fired after each selection.
 * opts.autoSelectDefault (default true) — sets AppState.TENANT/ENV to
 * esampark/production on first render if nothing is selected yet, so a
 * pill is always active.
 */
function renderEnvSelector(container, opts) {
  opts = opts || {};
  var onSelect = opts.onSelect || function () {};
  var autoSelectDefault = opts.autoSelectDefault !== false;
  var el = typeof container === 'string' ? document.getElementById(container) : container;
  if (!el) return;

  injectEnvSelectorStyles();

  if (autoSelectDefault && (!AppState.TENANT || !AppState.ENV)) {
    setEnvironment('esampark', 'production');
  }

  var tenantKeys = Object.keys(ENVIRONMENTS);
  var stageKeys = ['production', 'uat'];

  function tenantPillHTML(tenantKey) {
    var t = ENVIRONMENTS[tenantKey];
    var active = AppState.TENANT === tenantKey;
    return '<button type="button" class="bf-env-pill' + (active ? ' active' : '') + '" data-tenant="' + tenantKey + '">' +
      (t.icon ? t.icon + ' ' : '') + t.label + '</button>';
  }
  function stagePillHTML(stageKey) {
    var active = AppState.ENV === stageKey;
    var isProd = stageKey === 'production';
    return '<button type="button" class="bf-env-pill ' + (isProd ? 'bf-env-pill-prod' : 'bf-env-pill-uat') + (active ? ' active' : '') +
      '" data-stage="' + stageKey + '">' + (isProd ? '🟢 Production' : '🟠 UAT') + '</button>';
  }

  el.innerHTML =
    '<div class="bf-env-selector">' +
      '<div class="bf-env-row">' +
        '<span class="bf-env-row-label">Tenant</span>' +
        '<div class="bf-env-pills" data-group="tenant">' + tenantKeys.map(tenantPillHTML).join('') + '</div>' +
      '</div>' +
      '<div class="bf-env-row">' +
        '<span class="bf-env-row-label">Stage</span>' +
        '<div class="bf-env-pills" data-group="stage">' + stageKeys.map(stagePillHTML).join('') + '</div>' +
      '</div>' +
      '<div class="bf-env-preview" id="bf-env-preview-url"></div>' +
    '</div>';

  function updatePreview() {
    var previewEl = el.querySelector('#bf-env-preview-url');
    if (!previewEl) return;
    var url = getEnvironmentUrl(AppState.TENANT, AppState.ENV);
    previewEl.innerHTML = url ? ('🔗 <b>' + url.replace('https://', '') + '</b>') : 'Select an environment';
  }
  updatePreview();

  el.querySelectorAll('[data-tenant]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var tenantKey = btn.getAttribute('data-tenant');
      var stageKey = AppState.ENV || 'production';
      var url = setEnvironment(tenantKey, stageKey);
      el.querySelectorAll('[data-tenant]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      updatePreview();
      onSelect(tenantKey, stageKey, url);
    });
  });
  el.querySelectorAll('[data-stage]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var stageKey = btn.getAttribute('data-stage');
      var tenantKey = AppState.TENANT || 'esampark';
      var url = setEnvironment(tenantKey, stageKey);
      el.querySelectorAll('[data-stage]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      updatePreview();
      onSelect(tenantKey, stageKey, url);
    });
  });
}

// ---------------------------------------------------------
// API header builders
// ---------------------------------------------------------
function apiH() {
  return {
    'Authorization': 'Bearer ' + AppState.TOKEN,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Client-Type': 'Web'
  };
}
function apiHV() {
  return {
    'Authorization': 'Bearer ' + AppState.TOKEN,
    'Content-Type': 'application/vnd.api+json',
    'Accept': 'application/json',
    'X-Client-Type': 'Web'
  };
}
// ---------------------------------------------------------
// Excel helpers (xlsx-js-style must already be loaded as window.XLSX;
// login.js or index.js should have injected the <script> tag for it
// before any module calls downloadExcel)
// ---------------------------------------------------------
function downloadExcel(filename, sheets) {
  var wb = XLSX.utils.book_new();
  wb.Workbook = { Sheets: [] };
  sheets.forEach(function (sheet, sheetIdx) {
    // OPTIONAL: sheet.groupHeaders = [{ label: 'Basic Information', span: 16 }, ...]
    // Inserts one merged "section banner" row ABOVE the normal column
    // headers, covering `span` columns each, in order. Sheets that don't
    // set this behave exactly as before (no group row, header row 0).
    var hasGroups = sheet.groupHeaders && sheet.groupHeaders.length;
    var headerRowIdx = hasGroups ? 1 : 0;
    var aoa = [];
    if (hasGroups) {
      var groupRow = [];
      sheet.groupHeaders.forEach(function (g) {
        groupRow.push(g.label);
        for (var i = 1; i < g.span; i++) groupRow.push('');
      });
      aoa.push(groupRow);
    }
    aoa.push(sheet.headers);
    sheet.rows.forEach(function (r) { aoa.push(r); });
    var ws = XLSX.utils.aoa_to_sheet(aoa);
    if (hasGroups) {
      ws['!merges'] = ws['!merges'] || [];
      var col = 0;
      sheet.groupHeaders.forEach(function (g) {
        var startCol = col, endCol = col + g.span - 1;
        if (endCol > startCol) ws['!merges'].push({ s: { r: 0, c: startCol }, e: { r: 0, c: endCol } });
        var ref = XLSX.utils.encode_cell({ r: 0, c: startCol });
        if (!ws[ref]) ws[ref] = { t: 's', v: g.label };
        ws[ref].s = {
          fill: { patternType: 'solid', fgColor: { rgb: g.color || 'D9C9A3' } },
          font: { bold: true, color: { rgb: '3F3117' } },
          alignment: { horizontal: 'center', vertical: 'center' }
        };
        col = endCol + 1;
      });
    }
    sheet.headers.forEach(function (h, colIdx) {
      var ref = XLSX.utils.encode_cell({ r: headerRowIdx, c: colIdx });
      if (!ws[ref]) ws[ref] = { t: 's', v: h };
      var isInput = sheet.highlightCols && sheet.highlightCols.indexOf(colIdx) !== -1;
      // OPTIONAL: sheet.headerColors = [{ bg:'16A34A', font:'FFFFFF' }, ...]
      // one entry per column — colors that specific header cell instead of
      // the default blue/pink. More robust than merged group banners since
      // it needs no cell-merge support from whatever app opens the file.
      var custom = sheet.headerColors && sheet.headerColors[colIdx];
      var bg = custom ? custom.bg : (isInput ? 'FFC7CE' : '1D4ED8');
      var font = custom ? custom.font : (isInput ? '000000' : 'FFFFFF');
      ws[ref].s = {
        fill: { patternType: 'solid', fgColor: { rgb: bg } },
        font: { bold: true, color: { rgb: font } },
        alignment: { horizontal: 'center' }
      };
    });
    ws['!cols'] = sheet.headers.map(function (h, i) {
      var maxLen = Math.max(String(h || '').length, Math.max.apply(null, sheet.rows.map(function (r) { return String(r[i] == null ? '' : r[i]).length; }).concat([0])));
      return { wch: Math.min(Math.max(maxLen + 2, 10), 45) };
    });
    if (hasGroups) ws['!rows'] = [{ hpt: 20 }];
    wb.Workbook.Sheets[sheetIdx] = {};
    if (sheet.tabColor) wb.Workbook.Sheets[sheetIdx].TabColor = { rgb: sheet.tabColor };
    XLSX.utils.book_append_sheet(wb, ws, sheet.name.substring(0, 31));
  });
  XLSX.writeFile(wb, filename);
  // Audit is loaded after common.js, but by the time a user actually
  // triggers a download, bootstrap has long finished — safe to check lazily.
  if (AppCtx.Audit && typeof AppCtx.Audit.onDownload === 'function') {
    AppCtx.Audit.onDownload(filename);
  }
}
function readUploadedFile(file) {
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.onload = function (e) {
      try {
        var wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array' });
        var ws = wb.Sheets[wb.SheetNames[0]];
        var rows = XLSX.utils.sheet_to_json(ws, { defval: '', raw: false });
        resolve(rows);
      } catch (err) { reject(err); }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}
/**
 * wireFileInput — shows a file-info chip + Remove button after
 * selection, stores parsed rows in AppState.cache[holderKey].
 */
function wireFileInput(inputId, labelTextId, submitBtnId, holderKey) {
  var input = document.getElementById(inputId);
  var submitEl = document.getElementById(submitBtnId);
  var infoId = inputId + '-info';
  if (!document.getElementById(infoId)) {
    var info = document.createElement('div');
    info.id = infoId;
    info.className = 'bf-file-info';
    info.style.display = 'none';
    info.innerHTML = '<span class="fi-name" id="' + inputId + '-fname"></span>' +
      '<button class="bf-remove-btn" id="' + inputId + '-stop" type="button" style="margin-right:6px;">⏹ Stop</button>' +
      '<button class="bf-remove-btn" id="' + inputId + '-remove" type="button">✕ Remove</button>';
    input.parentNode.insertBefore(info, input.nextSibling);
  }
  function resetFile() {
    input.value = '';
    var labelSpan = document.getElementById(labelTextId);
    if (labelSpan) labelSpan.textContent = '📂 Click to select file (.xlsx)';
    var labelEl = document.querySelector('label[for="' + inputId + '"]');
    if (labelEl) labelEl.style.display = 'block';
    var infoEl = document.getElementById(infoId);
    if (infoEl) infoEl.style.display = 'none';
    submitEl.disabled = true;
    AppState.cache[holderKey] = null;
    AppState.cache[holderKey + '__cancelled'] = false;
  }
  input.addEventListener('change', function (e) {
    var file = e.target.files[0];
    if (!file) { resetFile(); return; }
    var labelEl = document.querySelector('label[for="' + inputId + '"]');
    if (labelEl) labelEl.style.display = 'none';
    document.getElementById(inputId + '-fname').textContent = '📄 ' + file.name;
    document.getElementById(infoId).style.cssText = 'display:flex;';
    AppState.cache[holderKey + '__cancelled'] = false; // fresh file → clear any earlier cancel flag
    readUploadedFile(file).then(function (rows) {
      AppState.cache[holderKey] = rows;
      submitEl.disabled = false;
      if (AppCtx.Audit && typeof AppCtx.Audit.onFileSelected === 'function') {
        AppCtx.Audit.onFileSelected(file.name);
      }
    }).catch(function (err) {
      if (AppCtx.Notifications && typeof AppCtx.Notifications.alert === 'function') {
        AppCtx.Notifications.alert('❌ Failed to read file: ' + err.message);
      } else {
        alert('❌ Failed to read file: ' + err.message);
      }
      resetFile();
    });
  });
  var removeBtn = document.getElementById(inputId + '-remove');
  if (removeBtn) removeBtn.addEventListener('click', function (e) { e.stopPropagation(); resetFile(); });
  // "⏹ Stop" — does NOT clear the selected file (so it can be re-submitted),
  // it just raises a flag that a running bulk-submit loop can check between
  // rows to abort early. See isUploadCancelled()/cancelUpload() below.
  var stopBtn = document.getElementById(inputId + '-stop');
  if (stopBtn) stopBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    cancelUpload(holderKey);
    if (AppCtx.Notifications && typeof AppCtx.Notifications.alert === 'function') {
      AppCtx.Notifications.alert('⏹ Stop requested — the upload will halt after the row currently in progress finishes.');
    }
  });
}
/**
 * Call this from a module's bulk-submit loop, once per row, e.g.:
 *   if (isUploadCancelled('sts')) { /* break out, show a partial-results summary *\/ }
 * `holderKey` is the same string passed as the 4th argument to wireFileInput().
 */
function isUploadCancelled(holderKey) {
  return !!(AppState.cache && AppState.cache[holderKey + '__cancelled']);
}
/** Sets the cancellation flag for a given upload — normally triggered by
 *  the "⏹ Stop" button wireFileInput() adds automatically, but modules
 *  may also call this directly (e.g. from their own custom Cancel button). */
function cancelUpload(holderKey) {
  AppState.cache[holderKey + '__cancelled'] = true;
}
// ---------------------------------------------------------
// Error / value parsing helpers
// ---------------------------------------------------------
function parseApiError(text) {
  if (!text) return 'Unknown error';
  var s = typeof text === 'string' ? text : JSON.stringify(text);
  try {
    var obj = JSON.parse(s);
    if (Array.isArray(obj.violations) && obj.violations.length) {
      return obj.violations.map(function (v) { return v.message || v.field || ''; }).filter(Boolean).join(', ');
    }
    if (obj.message && obj.message !== 'error.validation') return obj.message;
    if (obj.detail) return obj.detail;
    if (obj.title) return obj.title;
    if (obj.error) return obj.error;
  } catch (e) { /* not JSON */ }
  return s.substring(0, 200).trim();
}
function parseIntSafe(x) {
  var n = parseInt(parseFloat(x));
  return isNaN(n) ? null : n;
}
function cleanTaskId(val) {
  if (val === null || val === undefined) return '';
  var s = String(val).trim();
  if (/^\d+\.0+$/.test(s)) s = String(parseInt(parseFloat(s)));
  return s;
}
function formatValue(val) {
  if (val === null || val === undefined) return '';
  var s = String(val).trim();
  if (s.indexOf('.0', s.length - 2) !== -1) {
    var n = parseFloat(s);
    if (!isNaN(n) && Number.isInteger(n)) return String(parseInt(n));
  }
  return s;
}
// ---------------------------------------------------------
// Shared cross-module reference fetches
// ---------------------------------------------------------
function fetchPaycodesRef() {
  return fetch(AppState.BASE_URL + '/api/attendance/paycodes', { headers: apiH() })
    .then(function (r) { return r.ok ? r.json() : []; })
    .catch(function () { return []; });
}
function fetchPaycodeEventsRef() {
  return fetch(AppState.BASE_URL + '/api/attendance/paycode_events', { headers: apiH() })
    .then(function (r) { return r.ok ? r.json() : []; })
    .catch(function () { return []; });
}
/**
 * Shared "lookup table" fetch used by employee-lookup.js and org-lookup.js.
 */
function fetchLookupTable(getUrl) {
  return fetch(getUrl, { headers: apiH() }).then(function (r) {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }).then(function (raw) {
    var headersMeta = (raw.headers || []).sort(function (a, b) { return (a.sequence || 999) - (b.sequence || 999); });
    return { headersMeta: headersMeta, data: raw.content || raw.data || [] };
  });
}
/**
 * Shared employee-id resolution by externalNumber (used by ot-approval.js).
 * GET /api/attendance/employees/?externalNumber.equals={ext}
 */
function resolveEmployeeId(externalNumber) {
  return fetch(AppState.BASE_URL + '/api/attendance/employees/?externalNumber.equals=' + encodeURIComponent(externalNumber), { headers: apiH() })
    .then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error('Employee lookup failed — HTTP ' + r.status + ': ' + t.substring(0, 120)); });
      return r.json();
    })
    .then(function (data) {
      var list = Array.isArray(data) ? data : (data.content || data.data || []);
      if (!list.length) throw new Error('No employee found for externalNumber "' + externalNumber + '"');
      return list[0].id;
    });
}
// =========================================================
// Shared "policy set" module builder — used by shift-template-sets.js,
// accrual-policy-sets.js, and timeoff-policy-sets.js. All three follow
// the identical pattern from the legacy monolith:
//   - rows grouped by set_id (PUT update) or set_name (POST create)
//   - each row is one "entry" referencing an id (paycode/policy/template)
//
// cfg = { id, icon, title, baseUrl(), refUrl(), refName, colName,
//         entryKey, tabColor }
// =========================================================
function buildPolicySetModule(ctx, cfg) {
  var Notifications = ctx.Notifications;
  var Router = ctx.Router;
  var Audit = ctx.Audit;
  var modal = ctx.modal;
  var P = cfg.id;
  var icon = cfg.icon;
  var BASE = cfg.baseUrl;
  var REF = cfg.refUrl;
  var UPLOAD_HEADERS = ['set_id', 'set_name', 'set_description', 'entry_id', 'priority', cfg.colName];
  var INPUT_COLS = [1, 4, 5];
  if (!document.getElementById('screen-' + P)) {
    var main = document.createElement('div');
    main.id = 'screen-' + P; main.style.display = 'none';
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">' + icon + ' ' + cfg.title + '</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">' + icon + '</div><div><div class="mh-title">' + cfg.title + '</div><div class="mh-sub">Create · View · Delete</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="' + P + '-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Headers · existing sets · ' + cfg.refName + ' master</div></div>' +
        '<div class="bf-action-card" id="' + P + '-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Multiple rows per set_name = multiple entries</div></div>' +
        '<div class="bf-action-card" id="' + P + '-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Fetch all sets and download as Excel</div></div>' +
        '<div class="bf-action-card" id="' + P + '-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete sets by comma-separated IDs</div></div>' +
      '</div>';
    modal.appendChild(main);
    var create = document.createElement('div');
    create.id = 'screen-' + P + '-create'; create.style.display = 'none';
    create.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-' + P + '">' + icon + ' ' + cfg.title + '</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>' +
      '<div class="bf-info-box">Leave <b>set_id</b> blank to create. Fill <b>set_id</b> to update. Multiple rows with the same set_id/set_name = multiple entries in one set.</div>' +
      '<div id="' + P + '-create-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="' + P + '-file"><span id="' + P + '-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="' + P + '-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="' + P + '-c-prog"><div class="bf-pb" id="' + P + '-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="' + P + '-create-log"></div>' +
      '<button class="bf-btn bf-success" id="' + P + '-submit" disabled>🚀 Submit ' + cfg.title + '</button>' +
      '<button class="bf-btn bf-outline" id="' + P + '-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="' + P + '-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(create);
    var view = document.createElement('div');
    view.id = 'screen-' + P + '-view'; view.style.display = 'none';
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-' + P + '">' + icon + ' ' + cfg.title + '</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>' +
      '<div id="' + P + '-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="' + P + '-v-prog" style="display:none"><div class="bf-pb" id="' + P + '-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="' + P + '-fetch">⬇️ Download ' + cfg.title + '</button>';
    modal.appendChild(view);
    var del = document.createElement('div');
    del.id = 'screen-' + P + '-delete'; del.style.display = 'none';
    del.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-' + P + '">' + icon + ' ' + cfg.title + '</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>' +
      '<div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>' +
      '<div id="' + P + '-delete-status" class="bf-status"></div>' +
      '<label class="bf-label">Set IDs to delete (comma-separated)</label>' +
      '<input type="text" id="' + P + '-del-ids" placeholder="143, 144" />' +
      '<label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="' + P + '-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>' +
      '<div class="bf-log" id="' + P + '-delete-log"></div>' +
      '<button class="bf-btn bf-danger" id="' + P + '-do-delete" style="margin-top:10px;">🗑️ Delete</button>';
    modal.appendChild(del);
    Router.register('screen-' + P, 'screen-' + P + '-create', 'screen-' + P + '-view', 'screen-' + P + '-delete');
    [main, create, view, del].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll('input,textarea').forEach(function (inp) {
        ['keydown', 'keyup', 'keypress', 'input'].forEach(function (evt) { inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true); });
      });
    });
  }
  function fetchRef() {
    return fetch(REF(), { headers: apiH() }).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; });
  }
  document.getElementById(P + '-action-tpl').onclick = function () {
    var btn = document.getElementById(P + '-action-tpl'); btn.style.opacity = '0.6';
    Promise.all([
      fetch(BASE() + '?projection=FULL', { headers: apiH() }).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; }),
      fetchRef()
    ]).then(function (results) {
      var existing = results[0] || [];
      var refs = results[1] || [];
      var existRows = [];
      existing.forEach(function (set) {
        if (!(set.entries || []).length) existRows.push([set.id, set.name || '', set.description || '', '', '']);
        else set.entries.forEach(function (entry) {
          var policy = entry[cfg.entryKey] || {};
          existRows.push([set.id, set.name || '', set.description || '', entry.id || '', policy.id || '']);
        });
      });
      downloadExcel(P + '_template.xlsx', [
        { name: 'Upload_Template', tabColor: cfg.tabColor, headers: UPLOAD_HEADERS, rows: [], highlightCols: INPUT_COLS },
        { name: 'Existing_Sets_Ref', tabColor: '7C3AED', headers: ['set_id', 'set_name', 'set_description', 'entry_id', cfg.colName], rows: existRows },
        { name: cfg.refName.replace(/ /g, '_') + '_Master', tabColor: '059669', headers: ['id', 'name', 'description'], rows: refs.map(function (p) { return [p.id, p.name || '', p.description || '']; }) }
      ]);
      btn.style.opacity = '1';
    });
  };
  document.getElementById(P + '-action-create').onclick = function () {
    Notifications.clearLog(P + '-create-log');
    AppState.cache[P] = null; AppState.cache[P + 'SuccessRows'] = []; AppState.cache[P + 'FailedRows'] = [];
    document.getElementById(P + '-submit').disabled = true;
    document.getElementById(P + '-dl-success').style.display = 'none';
    document.getElementById(P + '-dl-failed').style.display = 'none';
    Router.go('screen-' + P + '-create');
  };
  document.getElementById(P + '-action-view').onclick = function () { Router.go('screen-' + P + '-view'); };
  document.getElementById(P + '-action-delete').onclick = function () { Notifications.clearLog(P + '-delete-log'); Router.go('screen-' + P + '-delete'); };
  wireFileInput(P + '-file', P + '-file-name', P + '-submit', P);
  document.getElementById(P + '-dl-success').onclick = function () {
    downloadExcel(P + '_success.xlsx', [{ name: 'Success', tabColor: '059669', headers: ['created_id', 'set_name', 'entries_count'], rows: (AppState.cache[P + 'SuccessRows'] || []).map(function (r) { return [r.id || '', r.name, r.entries]; }) }]);
  };
  document.getElementById(P + '-dl-failed').onclick = function () {
    downloadExcel(P + '_failed.xlsx', [{ name: 'Failed', tabColor: 'DC2626', headers: ['set_name', 'http_status', 'error'], rows: (AppState.cache[P + 'FailedRows'] || []).map(function (r) { return [r.name, r.status || '', r.error || '']; }) }]);
  };
  document.getElementById(P + '-submit').onclick = function () {
    var btn = document.getElementById(P + '-submit');
    var rows = AppState.cache[P] || [];
    Notifications.clearLog(P + '-create-log');
    document.getElementById(P + '-dl-success').style.display = 'none';
    document.getElementById(P + '-dl-failed').style.display = 'none';
    if (!rows.length) { Notifications.error(P + '-create-status', '❌ No data found'); return; }
    function col(row, name) {
      var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
      return k ? String(row[k] || '').trim() : '';
    }
    var updateGroups = {}, createGroups = {};
    rows.forEach(function (row) {
      var setId = parseIntSafe(col(row, 'set_id'));
      if (setId !== null) { if (!updateGroups[setId]) updateGroups[setId] = []; updateGroups[setId].push(row); }
      else { var setName = col(row, 'set_name'); if (!setName) return; if (!createGroups[setName]) createGroups[setName] = []; createGroups[setName].push(row); }
    });
    var updateEntries = Object.keys(updateGroups).map(function (k) { return [k, updateGroups[k]]; });
    var createEntries = Object.keys(createGroups).map(function (k) { return [k, createGroups[k]]; });
    var total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error(P + '-create-status', '❌ No valid groups'); return; }
    Notifications.loading(btn, 'Submitting...');
    Notifications.progress.show(P + '-c-prog');
    AppState.cache[P + 'SuccessRows'] = []; AppState.cache[P + 'FailedRows'] = [];
    var s = 0, f = 0, done = 0;
    function processUpdate(i) {
      if (i >= updateEntries.length) return processCreate(0);
      var setId = updateEntries[i][0], group = updateEntries[i][1];
      var first = group[0];
      var payload = { id: parseInt(setId), name: col(first, 'set_name'), description: col(first, 'set_description') || col(first, 'set_name'), entries: [] };
      var seen = {};
      group.forEach(function (row) {
        var entryId = parseIntSafe(col(row, 'entry_id'));
        var priority = parseIntSafe(col(row, 'priority')) || 1;
        var policyId = parseIntSafe(col(row, cfg.colName));
        if (!policyId) return;
        var key = entryId + '-' + policyId; if (seen[key]) return; seen[key] = true;
        var entry = {}; entry[cfg.entryKey] = { id: policyId }; entry.priority = priority; if (entryId !== null) entry.id = entryId;
        payload.entries.push(entry);
      });
      fetch(BASE() + '/' + payload.id, { method: 'PUT', headers: apiH(), body: JSON.stringify(payload) }).then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) { Notifications.log(P + '-create-log', '✅ Updated: ' + payload.name + ' (' + payload.entries.length + ' entries)', 'ok'); s++; if (Audit) Audit.onDbOp('updated', 1); AppState.cache[P + 'SuccessRows'].push({ id: payload.id, name: payload.name, entries: payload.entries.length }); }
          else { Notifications.log(P + '-create-log', '❌ Failed update: ' + payload.name + ' — ' + parseApiError(body), 'fail'); f++; AppState.cache[P + 'FailedRows'].push({ name: payload.name, status: r.status, error: parseApiError(body) }); }
        });
      }).catch(function (e) {
        Notifications.log(P + '-create-log', '❌ Error: ' + e.message, 'fail'); f++; AppState.cache[P + 'FailedRows'].push({ name: payload.name || '', status: 'ERR', error: e.message });
      }).then(function () {
        done++; Notifications.progress.set(P + '-c-bar', (done / total) * 100);
        processUpdate(i + 1);
      });
    }
    function processCreate(i) {
      if (i >= createEntries.length) return finish();
      var setName = createEntries[i][0], group = createEntries[i][1];
      var first = group[0];
      var payload = { name: setName, description: col(first, 'set_description') || setName, entries: [] };
      var seen = {};
      group.forEach(function (row) {
        var priority = parseIntSafe(col(row, 'priority')) || 1;
        var policyId = parseIntSafe(col(row, cfg.colName));
        if (!policyId || seen[policyId]) return; seen[policyId] = true;
        var entry = {}; entry[cfg.entryKey] = { id: policyId }; entry.priority = priority;
        payload.entries.push(entry);
      });
      fetch(BASE() + '/', { method: 'POST', headers: apiH(), body: JSON.stringify(payload) }).then(function (r) {
        return r.text().then(function (body) {
          var createdId = ''; try { createdId = JSON.parse(body).id || ''; } catch (e) {}
          if (r.ok) { Notifications.log(P + '-create-log', '✅ Created: ' + payload.name + ' (' + payload.entries.length + ' entries)', 'ok'); s++; if (Audit) Audit.onDbOp('created', 1); AppState.cache[P + 'SuccessRows'].push({ id: createdId, name: payload.name, entries: payload.entries.length }); }
          else { Notifications.log(P + '-create-log', '❌ Failed create: ' + payload.name + ' — ' + parseApiError(body), 'fail'); f++; AppState.cache[P + 'FailedRows'].push({ name: payload.name, status: r.status, error: parseApiError(body) }); }
        });
      }).catch(function (e) {
        Notifications.log(P + '-create-log', '❌ Error: ' + e.message, 'fail'); f++; AppState.cache[P + 'FailedRows'].push({ name: setName, status: 'ERR', error: e.message });
      }).then(function () {
        done++; Notifications.progress.set(P + '-c-bar', (done / total) * 100);
        processCreate(i + 1);
      });
    }
    function finish() {
      Notifications.log(P + '-create-log', '━━━━━━━━━━━━━━━━━━', 'info');
      Notifications.log(P + '-create-log', '✅ Success: ' + s + '  ❌ Failed: ' + f, f === 0 ? 'ok' : 'info');
      Notifications.status(P + '-create-status', 'Done — ' + s + ' success, ' + f + ' failed', f === 0 ? 'success' : 'info');
      Notifications.doneLoading(btn, '🚀 Submit ' + cfg.title);
      Notifications.progress.hide(P + '-c-prog');
      if (AppState.cache[P + 'SuccessRows'].length) document.getElementById(P + '-dl-success').style.display = 'block';
      if (AppState.cache[P + 'FailedRows'].length) document.getElementById(P + '-dl-failed').style.display = 'block';
    }
    processUpdate(0);
  };
  document.getElementById(P + '-fetch').onclick = function () {
    var btn = document.getElementById(P + '-fetch');
    Notifications.loading(btn, 'Connecting...');
    Notifications.progress.show(P + '-v-prog');
    Notifications.info(P + '-view-status', '⏳ Fetching data...'); Notifications.progress.set(P + '-v-bar', 25);
    fetch(BASE() + '?projection=FULL', { headers: apiH() }).then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error('HTTP ' + r.status + ': ' + parseApiError(t)); });
      return r.json();
    }).then(function (data) {
      if (!data.length) { Notifications.info(P + '-view-status', 'ℹ️ No records available to download.'); return; }
      Notifications.info(P + '-view-status', '⏳ Processing ' + data.length + ' set(s)...'); Notifications.progress.set(P + '-v-bar', 60);
      var rows = [];
      data.forEach(function (set) {
        if (!(set.entries || []).length) rows.push([set.id, set.name || '', set.description || '', '', '']);
        else set.entries.forEach(function (entry) {
          var policy = entry[cfg.entryKey] || {};
          rows.push([set.id, set.name || '', set.description || '', entry.id || '', policy.id || '']);
        });
      });
      Notifications.info(P + '-view-status', '⏳ Preparing Excel...'); Notifications.progress.set(P + '-v-bar', 85);
      downloadExcel(P + '_existing_' + new Date().toISOString().slice(0, 10) + '.xlsx', [{
        name: cfg.title.replace(/ /g, '_'), tabColor: cfg.tabColor,
        headers: ['set_id', 'set_name', 'set_description', 'entry_id', cfg.colName], rows: rows
      }]);
      Notifications.progress.set(P + '-v-bar', 100);
      Notifications.success(P + '-view-status', '✅ Download complete — ' + data.length + ' set(s)');
    }).catch(function (e) {
      Notifications.error(P + '-view-status', '❌ ' + e.message); Notifications.progress.set(P + '-v-bar', 0);
    }).then(function () {
      Notifications.doneLoading(btn, '⬇️ Download ' + cfg.title);
      Notifications.progress.hide(P + '-v-prog', 2000);
    });
  };
  document.getElementById(P + '-do-delete').onclick = function () {
    if (!document.getElementById(P + '-confirm').checked) { Notifications.error(P + '-delete-status', '⚠️ Check confirmation box'); return; }
    var ids = document.getElementById(P + '-del-ids').value.split(',').map(function (s) { return s.trim(); }).filter(function (s) { return s !== ''; });
    if (!ids.length) { Notifications.error(P + '-delete-status', '❌ No IDs entered'); return; }
    var btn = document.getElementById(P + '-do-delete');
    Notifications.loading(btn, 'Deleting...'); Notifications.clearLog(P + '-delete-log');
    var s = 0, f = 0;
    function next(i) {
      if (i >= ids.length) {
        if (Audit) Audit.onDbOp('deleted', s);
        Notifications.status(P + '-delete-status', 'Done — ' + s + ' deleted, ' + f + ' failed', f === 0 ? 'success' : 'info');
        Notifications.doneLoading(btn, '🗑️ Delete');
        return;
      }
      var id = ids[i];
      fetch(BASE() + '/' + id, { method: 'DELETE', headers: apiH() }).then(function (r) {
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log(P + '-delete-log', '✅ Deleted: ' + id, 'ok'); s++; next(i + 1); }
        else return r.text().then(function (t) { Notifications.log(P + '-delete-log', '❌ Failed: ' + id + ' — ' + parseApiError(t), 'fail'); f++; next(i + 1); });
      }).catch(function (e) { Notifications.log(P + '-delete-log', '❌ Error: ' + id + ' — ' + e.message, 'fail'); f++; next(i + 1); });
    }
    next(0);
  };
}
// ---------------------------------------------------------
// Expose everything on AppCtx (nothing is a real ES export)
// ---------------------------------------------------------
AppCtx.BASIC_AUTH = BASIC_AUTH;
AppCtx.TOKEN_VALIDITY_MIN = TOKEN_VALIDITY_MIN;
AppCtx.ENVIRONMENTS = ENVIRONMENTS;
AppCtx.AppState = AppState;
AppCtx.setEnvironment = setEnvironment;
AppCtx.getEnvironmentUrl = getEnvironmentUrl;
AppCtx.renderEnvSelector = renderEnvSelector;
AppCtx.apiH = apiH;
AppCtx.apiHV = apiHV;
AppCtx.downloadExcel = downloadExcel;
AppCtx.readUploadedFile = readUploadedFile;
AppCtx.wireFileInput = wireFileInput;
AppCtx.isUploadCancelled = isUploadCancelled;
AppCtx.cancelUpload = cancelUpload;
AppCtx.parseApiError = parseApiError;
AppCtx.parseIntSafe = parseIntSafe;
AppCtx.cleanTaskId = cleanTaskId;
AppCtx.formatValue = formatValue;
AppCtx.fetchPaycodesRef = fetchPaycodesRef;
AppCtx.fetchPaycodeEventsRef = fetchPaycodeEventsRef;
AppCtx.fetchLookupTable = fetchLookupTable;
AppCtx.resolveEmployeeId = resolveEmployeeId;
AppCtx.buildPolicySetModule = buildPolicySetModule;