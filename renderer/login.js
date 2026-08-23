/* =========================================================
 * login.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Load order: LAST of the core files (after common/router/audit/
 * notifications), so it's safe to read AppCtx.* at the top level here.
 * Owns: rendering the login screen + hub screen (module grid),
 * auth, logout, environment switching, token reuse.
 *
 * CHANGE LOG (session ID now sourced from audit.js, not duplicated):
 *   - REMOVED _genSessionId() — audit.js's Audit.startSession()
 *     already generates a real session ID (_genSID()) AND, as of
 *     this pass, fires the immediate LOGIN webhook message using
 *     it. Generating a second, different ID here would make the
 *     on-screen toast disagree with what was actually sent to the
 *     webhook, so login.js now uses Audit.startSession()'s RETURN
 *     VALUE as the single source of truth for AppState.SESSION_ID.
 *   - _doLogin(): AppState.SESSION_ID is now set from
 *     `Audit.startSession(user, envLabel)`'s return value (that
 *     call also triggers the immediate webhook send inside
 *     audit.js). The on-screen toast fires right after, using that
 *     same ID — so toast and webhook always match exactly.
 *   - loginInit()'s token-resume branch (`_tokenStillValid()`)
 *     already called `Audit.startSession(...)` when Audit wasn't
 *     active; its return value is now also captured into
 *     AppState.SESSION_ID for consistency, though the login toast
 *     itself intentionally does NOT fire on a resumed session (no
 *     fresh credentials were entered).
 *   - Everything else — top bar, session card, module cards/
 *     sections, footer, auth flow, IDs — UNCHANGED from the
 *     previous pass.
 * ========================================================= */
'use strict';
var AppState = AppCtx.AppState;
var BASIC_AUTH = AppCtx.BASIC_AUTH;
var ENVIRONMENTS = AppCtx.ENVIRONMENTS;
var TOKEN_VALIDITY_MIN = AppCtx.TOKEN_VALIDITY_MIN;
var Notifications = AppCtx.Notifications;
var Router = AppCtx.Router;
var Audit = AppCtx.Audit;
var modal = AppCtx.modal;

// Locally-tracked selection on the login screen, before it's committed
// to AppState (which only happens once a login attempt is fired).
var _selectedTenant = AppState.TENANT || 'esampark';
var _selectedStage = AppState.ENV || 'production';

function _envLabel(tenantKey, stageKey) {
  var tenant = ENVIRONMENTS[tenantKey];
  var stage = tenant && tenant[stageKey];
  if (!tenant || !stage) return tenantKey + ' / ' + stageKey;
  return (tenant.icon ? tenant.icon + ' ' : '') + tenant.label + ' — ' + stage.label;
}

/** Formats a Date as e.g. "04:40 PM" — used only for the on-screen
 *  toast; the webhook message's own timestamp formatting lives in
 *  audit.js (_hm/_dateStr), independently. */
function _fmtTime12(d) {
  var h = d.getHours(), m = d.getMinutes();
  var ampm = h >= 12 ? 'PM' : 'AM';
  var h12 = h % 12; if (h12 === 0) h12 = 12;
  return h12 + ':' + (m < 10 ? '0' : '') + m + ' ' + ampm;
}

// ---------------------------------------------------------
// Module categorization — built ONLY from the real ids present in
// AppCtx.MODULE_REGISTRY (index.js). Nothing here is invented; any
// module id not covered below automatically falls into "Other" so
// a future registry change can never silently hide a module. Each
// category also gets an accent color, used only for the icon-badge
// styling — purely decorative, no data implication.
// ---------------------------------------------------------
var MODULE_CATEGORIES = [
  { label: 'Time & Attendance', accent: 'blue', ids: ['timecard-update', 'punch', 'ot-approval', 'workflow-transfer', 'tasks'] },
  { label: 'Employee & Organization', accent: 'indigo', ids: ['employee-lookup', 'org-lookup', 'roles'] },
  { label: 'Paycodes & Events', accent: 'red', ids: ['paycodes', 'paycode-events', 'paycode-event-sets', 'paycode-combinations'] },
  { label: 'Shifts', accent: 'blue', ids: ['shift-templates', 'shift-template-sets'] },
  { label: 'Accruals & Time Off', accent: 'green', ids: ['accrual', 'accrual-policies', 'accrual-policy-sets', 'accrual-balances', 'timeoff-policy-sets', 'timeoff-policy-config', 'timeoff-raise'] },
  { label: 'Regularization & Outpass', accent: 'purple', ids: ['regularization-policies', 'regularization-policy-sets', 'outpass-policies', 'outpass-policy-sets'] }
];

// Short, neutral descriptions derived only from each module's existing
// name — no functionality is claimed beyond what the name implies.
var MODULE_DESCRIPTIONS = {
  'timecard-update': 'Update employee timecards.',
  'ot-approval': 'Review and approve overtime requests.',
  'workflow-transfer': 'Transfer workflows seamlessly.',
  'punch': 'Manage employee punch records.',
  'tasks': 'Track and manage your tasks.',
  'employee-lookup': 'Search employee information.',
  'org-lookup': 'Search organization structure.',
  'paycodes': 'Manage attendance paycodes.',
  'paycode-events': 'Manage paycode events.',
  'paycode-event-sets': 'Manage paycode event sets.',
  'paycode-combinations': 'Manage paycode combinations.',
  'shift-templates': 'Manage shift templates.',
  'shift-template-sets': 'Manage shift template sets.',
  'accrual': 'Manage accrual configurations.',
  'accrual-policies': 'Manage accrual policies.',
  'accrual-policy-sets': 'Manage accrual policy sets.',
  'timeoff-policy-sets': 'Manage time off policy sets.',
  'timeoff-policy-config': 'Configure time off policies.',
  'roles': 'Search organization structure.',
  'accrual-balances': 'View employee accrual balances.',
  'timeoff-raise': 'Raise time off requests.',
  'regularization-policies': 'Manage regularization policies.',
  'regularization-policy-sets': 'Manage regularization policy sets.',
  'outpass-policies': 'Manage outpass policies.',
  'outpass-policy-sets': 'Manage outpass policy sets.'
};

function _categorizedModules() {
  var used = {};
  var groups = MODULE_CATEGORIES.map(function (cat) {
    var mods = (AppCtx.MODULE_REGISTRY || []).filter(function (m) {
      if (cat.ids.indexOf(m.id) === -1) return false;
      used[m.id] = true;
      return true;
    });
    return { label: cat.label, accent: cat.accent, modules: mods };
  }).filter(function (c) { return c.modules.length > 0; });
  var leftover = (AppCtx.MODULE_REGISTRY || []).filter(function (m) { return !used[m.id]; });
  if (leftover.length) groups.push({ label: 'Other', accent: 'gray', modules: leftover });
  return groups;
}

function _moduleDesc(m) {
  return MODULE_DESCRIPTIONS[m.id] || ('Open the ' + m.name + ' module.');
}

/** One dashboard grid card. Keeps the SAME class (.bf-module-card) and
 *  data-module attribute the app has always used, so index.js's
 *  existing wireModuleCards() continues to work unmodified. */
function _cardHTML(m, accent) {
  var desc = _moduleDesc(m);
  return '<div class="bf-module-card" data-module="' + m.id + '">' +
    '<div class="mc-icon-badge mc-accent-' + accent + '">' + m.icon + '</div>' +
    '<div class="mc-body"><div class="mc-name">' + m.name + '</div>' +
    '<div class="mc-desc">' + desc + '</div></div>' +
    '<div class="mc-arrow">→</div>' +
  '</div>';
}

function _moduleSectionsHTML() {
  return _categorizedModules().map(function (cat) {
    return '<div class="bf-module-section">' +
      '<div class="bf-section-label bf-section-label-' + cat.accent + '">' + cat.label + '</div>' +
      '<div class="bf-module-grid">' + cat.modules.map(function (m) { return _cardHTML(m, cat.accent); }).join('') + '</div>' +
    '</div>';
  }).join('');
}

function _renderScreens() {
  var wrap = document.createElement('div');
  wrap.innerHTML =
    '<div id="screen-login">' +
      '<div class="bf-login-shell">' +
        '<div class="bf-login-card">' +
          '<div class="bf-logo">🐝</div>' +
          '<div class="bf-main-title">BeeForce Tools</div>' +
          '<div class="bf-main-sub">Sign in to continue</div>' +
          '<div class="bf-section-label" style="margin-top:6px;">Environment</div>' +
          '<div id="login-env-picker"></div>' +
          '<div id="login-status" class="bf-status"></div>' +
          '<label class="bf-label">Username</label>' +
          '<input type="text" id="login-user" placeholder="Enter username" autocomplete="username" />' +
          '<label class="bf-label">Password</label>' +
          '<input type="password" id="login-pass" placeholder="Enter password" autocomplete="current-password" />' +
          '<button class="bf-btn bf-primary" id="login-btn">🔐 Sign In</button>' +
        '</div>' +
      '</div>' +
    '</div>' +

    // ---- screen-hub: top-bar dashboard ----
    '<div id="screen-hub" style="display:none">' +
      '<div class="bf-dash">' +

        // Top bar
        '<div class="bf-dash-topbar">' +
          '<div class="bf-dash-brand"><span class="bf-dash-logo">🐝</span><span class="bf-dash-brand-name">BeeForce</span></div>' +
          '<div class="bf-dash-topbar-right">' +
            '<div class="bf-chip">' +
              '<div class="bf-chip-label">Environment</div>' +
              '<div class="bf-env-pill" id="hub-env-pill">—</div>' +
            '</div>' +
            '<div class="bf-chip bf-chip-conn">' +
              '<span class="bf-conn-dot"></span>' +
              '<div><div class="bf-chip-label">Connected to</div><div class="bf-chip-value" id="hub-base-url">—</div></div>' +
            '</div>' +
            '<div class="bf-user-badge">' +
              '<div class="bf-user-avatar" id="hub-avatar">U</div>' +
              '<div><div class="bf-user-name" id="hub-username">User</div>' +
              '<div class="bf-user-meta" id="hub-meta">Token active</div></div>' +
            '</div>' +
            '<button class="bf-btn bf-outline" id="hub-logout" type="button">🚪 Logout</button>' +
          '</div>' +
        '</div>' +

        '<div class="bf-main-scroll">' +
          '<div class="bf-shell-inner">' +

            // Session panel (only real fields)
            '<div class="bf-session-card">' +
              '<div class="bf-session-title">👤 Session</div>' +
              '<div class="bf-session-grid">' +
                '<div class="bf-session-row"><span>User ID</span><b id="hub-panel-userid">—</b></div>' +
                '<div class="bf-session-row"><span>Environment</span><b id="hub-panel-env">—</b></div>' +
                '<div class="bf-session-row"><span>Connected to</span><b id="hub-panel-url">—</b></div>' +
                '<div class="bf-session-row"><span>Session ID</span><b id="hub-panel-sid">—</b></div>' +
                '<div class="bf-session-row"><span>Session started</span><b id="hub-panel-started">—</b></div>' +
                '<div class="bf-session-row"><span>Session timeout</span><b id="hub-panel-timeout">—</b></div>' +
              '</div>' +
            '</div>' +

            '<div id="hub-module-sections">' + _moduleSectionsHTML() + '</div>' +

            '<div class="bf-dash-footer">' +
              '<div class="bf-footer-item"><span class="bf-footer-icon">🛡️</span><div><b>Secure. Reliable. Powerful.</b><div>BeeForce Tools — Your Workforce, Our Priority.</div></div></div>' +
              '<div class="bf-footer-item"><span class="bf-footer-icon">🎧</span><div><b>Need Help?</b><div>Contact your system administrator.</div></div></div>' +
              '<div class="bf-footer-item bf-footer-item-right"><span class="bf-footer-icon">🔒</span><div>© ' + new Date().getFullYear() + ' BeeForce Technologies. All rights reserved.</div></div>' +
            '</div>' +

          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';

  // Move the two screens into the modal (append after any loading screen).
  while (wrap.firstChild) modal.appendChild(wrap.firstChild);

  // Prevent host-page keyboard handlers / outside clicks from interfering.
  modal.querySelectorAll('input, textarea').forEach(function (el) {
    ['keydown', 'keyup', 'keypress', 'input'].forEach(function (evt) {
      el.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
    });
  });

  if (!modal.querySelector('.bf-close-btn')) {
    var closeBtn = document.createElement('button');
    closeBtn.className = 'bf-close-btn';
    closeBtn.id = 'bf-hub-close';
    closeBtn.textContent = '✕';
    modal.insertBefore(closeBtn, modal.firstChild);
    closeBtn.onclick = function () {
      AppCtx.overlay.remove();
      if (AppCtx.Styles) AppCtx.Styles.removeStyles();
    };
  }

  modal.addEventListener('click', function (e) { e.stopPropagation(); });
  modal.addEventListener('mousedown', function (e) { e.stopPropagation(); });
}

/** Fills in every real value on the dashboard (top bar + session
 *  panel). Every value here traces back to AppState / AppCtx —
 *  nothing is invented. AppState.SESSION_ID is set by _doLogin()/
 *  loginInit() from Audit.startSession()'s return value (see file
 *  header comment). */
function _populateDashboardData(username, ageMinutes, stageKey) {
  var envLabel = _envLabel(AppState.TENANT, AppState.ENV);
  var hostLabel = (AppState.BASE_URL || '').replace('https://', '');

  document.getElementById('hub-avatar').textContent = username.slice(0, 2).toUpperCase();
  document.getElementById('hub-username').innerHTML =
    username + ' <span class="bf-env-badge ' + (stageKey === 'uat' ? 'uat' : 'prod') + '">' + (stageKey === 'uat' ? 'UAT' : 'PROD') + '</span>';
  document.getElementById('hub-meta').textContent = 'Token active (' + (ageMinutes || 0) + 'm / ' + TOKEN_VALIDITY_MIN + 'm)';
  document.getElementById('hub-base-url').textContent = hostLabel || '—';

  var envPill = document.getElementById('hub-env-pill');
  if (envPill) {
    envPill.textContent = stageKey === 'uat' ? 'UAT' : 'PRODUCTION';
    envPill.className = 'bf-env-pill ' + (stageKey === 'uat' ? 'bf-env-pill-uat' : 'bf-env-pill-prod');
  }

  var elUid = document.getElementById('hub-panel-userid'); if (elUid) elUid.textContent = username;
  var elEnv = document.getElementById('hub-panel-env'); if (elEnv) elEnv.textContent = envLabel;
  var elUrl = document.getElementById('hub-panel-url'); if (elUrl) elUrl.textContent = hostLabel || '—';
  var elSid = document.getElementById('hub-panel-sid'); if (elSid) elSid.textContent = AppState.SESSION_ID || '—';
  var elStarted = document.getElementById('hub-panel-started');
  if (elStarted) {
    elStarted.textContent = AppState.TOKEN_ISSUED
      ? new Date(AppState.TOKEN_ISSUED).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
      : '—';
  }
  var elTimeout = document.getElementById('hub-panel-timeout'); if (elTimeout) elTimeout.textContent = TOKEN_VALIDITY_MIN + ' minutes';
}

function _showHub(username, ageMinutes, stageKey) {
  _populateDashboardData(username, ageMinutes, stageKey);
  Router.go('screen-hub');
}

function _tokenStillValid() {
  var age = (Date.now() - (AppState.TOKEN_ISSUED || 0)) / 1000 / 60;
  return AppState.TOKEN && AppState.TENANT && AppState.ENV && age < TOKEN_VALIDITY_MIN;
}

function _doLogin() {
  var btn = document.getElementById('login-btn');
  var user = document.getElementById('login-user').value.trim();
  var pass = document.getElementById('login-pass').value.trim();
  if (!user || !pass) { Notifications.error('login-status', 'Please enter both fields'); return; }
  var envUrl = AppCtx.getEnvironmentUrl(_selectedTenant, _selectedStage);
  if (!envUrl) { Notifications.error('login-status', 'Please select an environment'); return; }
  // Commit the selection to AppState.BASE_URL up front (same as the
  // original behavior — the request goes to whichever env is selected,
  // TENANT/ENV are only committed on a successful login below).
  AppState.BASE_URL = envUrl;
  var AUTH_URL = AppState.BASE_URL + '/api/authorization/oauth/token';
  var envLabel = _envLabel(_selectedTenant, _selectedStage);
  Notifications.loading(btn, 'Signing in to ' + envLabel + '...');
  fetch(AUTH_URL + '?username=' + encodeURIComponent(user) + '&password=' + encodeURIComponent(pass) + '&grant_type=password', {
    method: 'POST',
    headers: { 'Authorization': BASIC_AUTH, 'Content-Type': 'application/x-www-form-urlencoded' }
  }).then(function (r) {
    if (!r.ok) {
      return r.json().then(function (errBody) {
        var errMsg = 'HTTP ' + r.status;
        if (errBody.error === 'invalid_grant' || /bad.credentials/i.test(errBody.error_description || '')) {
          errMsg = 'Bad Credentials — The username or password you entered is incorrect. Please verify and try again.';
        } else if (errBody.error_description) errMsg = errBody.error_description;
        else if (errBody.error) errMsg = errBody.error;
        throw new Error(errMsg);
      }, function () { throw new Error('HTTP ' + r.status); });
    }
    return r.json();
  }).then(function (data) {
    if (!data.access_token) throw new Error('No token in response');
    AppCtx.setEnvironment(_selectedTenant, _selectedStage); // commits TENANT/ENV/BASE_URL together
    AppState.TOKEN = data.access_token;
    AppState.USERNAME = user; // Username captured HERE, at the moment of success — never lost afterward.
    AppState.TOKEN_ISSUED = Date.now();
    // Audit.startSession() generates the REAL session ID, sends the
    // immediate LOGIN webhook message (see audit.js), and returns
    // that same ID — captured here as the single source of truth.
    AppState.SESSION_ID = Audit.startSession(user, envLabel);
    _showHub(user, 0, _selectedStage);

    // On-screen confirmation toast — mirrors what was just sent to
    // the webhook, using the SAME session id and login timestamp.
    var loginTime = new Date(AppState.TOKEN_ISSUED);
    Notifications.toast({
      title: 'LOGIN',
      accent: 'red',
      duration: 6000,
      rows: [
        { icon: '👤', text: user },
        { icon: '🌐', text: _selectedStage === 'uat' ? 'UAT' : 'Production' },
        { icon: '🆔', text: AppState.SESSION_ID },
        { icon: '🕐', text: 'Login ' + _fmtTime12(loginTime) + ' — ' + loginTime.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) }
      ]
    });
  }).catch(function (e) {
    Notifications.error('login-status', '❌ ' + e.message);
  }).then(function () {
    Notifications.doneLoading(btn, '🔐 Sign In');
  });
}

function _doLogout() {
  Audit.endSession('LOGOUT');
  AppState.TOKEN = null;
  AppState.TENANT = null;
  AppState.ENV = null;
  AppState.USERNAME = null;
  AppState.SESSION_ID = null;
  var u = document.getElementById('login-user');
  var p = document.getElementById('login-pass');
  if (u) u.value = '';
  if (p) p.value = '';
  Router.go('screen-login');
}

function _loadXLSXIfNeeded() {
  if (window.XLSX) return Promise.resolve();
  return new Promise(function (resolve, reject) {
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js';
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

function loginInit() {
  _renderScreens();
  _loadXLSXIfNeeded().catch(function (e) { console.warn('[BF] Failed to load XLSX library', e); });
  AppCtx.renderEnvSelector(document.getElementById('login-env-picker'), {
    onSelect: function (tenantKey, stageKey) {
      _selectedTenant = tenantKey;
      _selectedStage = stageKey;
    }
  });
  document.getElementById('login-btn').onclick = _doLogin;
  document.getElementById('login-pass').addEventListener('keydown', function (e) {
    e.stopPropagation();
    if (e.key === 'Enter') _doLogin();
  }, true);
  document.getElementById('hub-logout').onclick = _doLogout;
  Router.wireDataGoLinks(modal);
  if (_tokenStillValid()) {
    _showHub(AppState.USERNAME || 'User', Math.floor((Date.now() - AppState.TOKEN_ISSUED) / 60000), AppState.ENV);
    // Resumed/still-valid session: only (re)start audit tracking if it
    // isn't already active — captures the SAME real sessionId into
    // AppState.SESSION_ID for consistency. Deliberately does NOT fire
    // the on-screen login toast here, since no fresh credentials were
    // entered in this branch.
    if (!Audit.active()) AppState.SESSION_ID = Audit.startSession(AppState.USERNAME, _envLabel(AppState.TENANT, AppState.ENV));
  } else {
    Router.go('screen-login');
  }
}

AppCtx.Login = {
  init: loginInit,
  logout: _doLogout,
  isTokenValid: _tokenStillValid
};