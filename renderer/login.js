/* =========================================================
 * login.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Load order: LAST of the core files (after common/router/audit/
 * notifications), so it's safe to read AppCtx.* at the top level here.
 * Owns: rendering the login screen + hub screen (module grid),
 * auth, logout, environment switching, token reuse.
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

function _moduleGridHTML() {
  return (AppCtx.MODULE_REGISTRY || []).map(function (m) {
    return '<div class="bf-module-card" data-module="' + m.id + '"><div class="mc-icon">' + m.icon + '</div><div class="mc-name">' + m.name + '</div></div>';
  }).join('\n');
}
function _renderScreens() {
  var wrap = document.createElement('div');
  wrap.innerHTML =
    '<div id="screen-login">' +
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
    '<div id="screen-hub" style="display:none">' +
      '<div class="bf-logo">🐝</div>' +
      '<div class="bf-main-title">BeeForce Tools</div>' +
      '<div class="bf-main-sub" id="hub-base-url">app.beeforce.in</div>' +
      '<div class="bf-user-badge">' +
        '<div class="bf-user-avatar" id="hub-avatar">U</div>' +
        '<div><div class="bf-user-name" id="hub-username">User</div>' +
        '<div class="bf-user-meta" id="hub-meta">Token active</div></div>' +
      '</div>' +
      '<div class="bf-section-label">Select a module</div>' +
      '<div class="bf-module-grid">' + _moduleGridHTML() + '</div>' +
      '<div class="bf-divider"></div>' +
      '<button class="bf-btn bf-outline" id="hub-logout">🚪 Logout / Switch Environment</button>' +
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
function _showHub(username, ageMinutes, stageKey) {
  document.getElementById('hub-avatar').textContent = username.slice(0, 2).toUpperCase();
  document.getElementById('hub-username').innerHTML =
    username + ' <span class="bf-env-badge ' + (stageKey === 'uat' ? 'uat' : 'prod') + '">' + (stageKey === 'uat' ? 'UAT' : 'PROD') + '</span>';
  document.getElementById('hub-meta').textContent = 'Token active (' + (ageMinutes || 0) + 'm / ' + TOKEN_VALIDITY_MIN + 'm)';
  document.getElementById('hub-base-url').textContent = AppState.BASE_URL.replace('https://', '');
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
    Audit.startSession(user, envLabel);
    _showHub(user, 0, _selectedStage);
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
    if (!Audit.active()) Audit.startSession(AppState.USERNAME, _envLabel(AppState.TENANT, AppState.ENV));
  } else {
    Router.go('screen-login');
  }
}
AppCtx.Login = {
  init: loginInit,
  logout: _doLogout,
  isTokenValid: _tokenStillValid
};