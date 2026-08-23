/* =========================================================
 * audit.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Load order: AFTER router.js, BEFORE notifications.js/login.js.
 * Owns: session tracking, API telemetry, and TWO webhook messages —
 * (1) an immediate LOGIN message the instant a session starts, and
 * (2) the ONE merged summary message sent at logout / tab-close /
 * token-expiry, exactly as before. Nothing about the summary report
 * changed; only the new immediate login send was added.
 *
 * CHANGE LOG (instant login webhook message):
 *   - NEW _dateStr(d): formats a timestamp as "Aug 23, 2026" in
 *     Asia/Kolkata, to pair with the existing _hm() time formatter.
 *   - NEW _buildLoginReport(): builds the small, immediate LOGIN
 *     message in the exact requested format:
 *       🔴 LOGIN
 *       ━━━━━━━━━━━━━━━━━━━━━━
 *       👤 <username>
 *       🌐 <environment>
 *       🆔 <sessionId>
 *       🕐 Login <HH:MM AM/PM> — <Mon DD, YYYY>
 *   - Audit.startSession() now sends this via _sendChunked()
 *     IMMEDIATELY after the session buffer is created (real
 *     sessionId/username/environment/loginTime — nothing invented).
 *   - Audit.startSession() still RETURNS the generated sessionId,
 *     exactly as before — login.js now uses that return value as
 *     the single source of truth for the session ID (see login.js
 *     header comment), instead of generating its own separately.
 *   - Everything else — _buildReport() (the full logout summary),
 *     ApiTracker, onModuleOpen/onFileSelected/onDownload/onDbOp/
 *     onValidationError/onApiError/onApiCall, the beforeunload/
 *     unhandledrejection listeners — is BYTE-FOR-BYTE unchanged.
 * ========================================================= */
'use strict';
var AUDIT_WEBHOOK_URL =
  'https://chat.googleapis.com/v1/spaces/AAQAf2F7sYM/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=w4-g6Zs-GZxG1CP5_VQ-M2oG1i8p7_Ku518ciTPTE-Y';
function _pad(n) { return String(n).length < 2 ? '0' + n : String(n); }
function _ts(d) {
  d = new Date(d || Date.now());
  return d.getFullYear() + '' + _pad(d.getMonth() + 1) + _pad(d.getDate()) + '-' + _pad(d.getHours()) + _pad(d.getMinutes()) + _pad(d.getSeconds());
}
var _IND = { timeZone: 'Asia/Kolkata', hour12: true, hour: '2-digit', minute: '2-digit' };
function _hm(d) { return new Date(d).toLocaleTimeString('en-IN', _IND); }
// NEW: date-only companion to _hm(), same timezone, e.g. "Aug 23, 2026".
function _dateStr(d) {
  return new Date(d).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', year: 'numeric' });
}
function _dur(ms) {
  var s = Math.floor(ms / 1000), m = Math.floor(s / 60), h = Math.floor(m / 60);
  if (h > 0) return h + 'h ' + (m % 60) + 'm ' + (s % 60) + 's';
  if (m > 0) return m + 'm ' + (s % 60) + 's';
  return s + 's';
}
function _genSID() { return 'SID-' + _ts() + '-' + Math.random().toString(36).slice(2, 6).toUpperCase(); }
function _xhrSend(text, attempt) {
  attempt = attempt || 1;
  var xhr = new XMLHttpRequest();
  xhr.open('POST', AUDIT_WEBHOOK_URL, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function () {
    if (xhr.status >= 200 && xhr.status < 300) {
      if (window.AUDIT_DEBUG) console.log('[Audit] ✅ sent');
    } else if (attempt < 3) {
      setTimeout(function () { _xhrSend(text, attempt + 1); }, 800 * Math.pow(attempt, 2));
    } else {
      console.debug('[Audit] webhook rejected', xhr.status);
    }
  };
  xhr.onerror = function () {
    if (attempt < 3) setTimeout(function () { _xhrSend(text, attempt + 1); }, 800 * Math.pow(attempt, 2));
    else console.debug('[Audit] webhook unreachable');
  };
  try { xhr.send(JSON.stringify({ text: text })); } catch (e) { console.debug('[Audit] XHR error', e.message); }
}
function _sendChunked(fullText) {
  var LIMIT = 3800;
  if (fullText.length <= LIMIT) { _xhrSend(fullText); return; }
  var lines = fullText.split('\n');
  var chunk = '';
  lines.forEach(function (line) {
    if ((chunk + line + '\n').length > LIMIT) { _xhrSend(chunk); chunk = ''; }
    chunk += line + '\n';
  });
  if (chunk.trim()) _xhrSend(chunk);
}
function _freshBuffer() {
  return {
    sessionId: null, username: null, environment: null,
    loginTime: null, logoutTime: null, duration: null,
    modulesVisited: [], uploadedFiles: [],
    downloads: { templates: 0, reports: 0, data: 0 },
    dbOperations: { created: 0, updated: 0, deleted: 0 },
    api: { GET: [], POST: [], PUT: [], PATCH: [], DELETE: [] },
    validationErrors: [], apiErrors: [], transactions: []
  };
}
var _sessionAudit = _freshBuffer();
var _txnCounter = 0;
function _genTxn() {
  _txnCounter++;
  var id = 'TXN-' + _ts() + '-' + ('00' + _txnCounter).slice(-3);
  _sessionAudit.transactions.push(id);
  return id;
}
// NEW: small, immediate message sent the instant a session starts.
// Uses ONLY real values already on the session buffer at that
// moment (sessionId/username/environment/loginTime) — nothing
// invented, no placeholder data.
function _buildLoginReport() {
  var S = _sessionAudit;
  var lines = [];
  lines.push('🔴 LOGIN');
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('👤 ' + (S.username || 'Unknown user'));
  lines.push('🌐 ' + (S.environment || 'Unknown'));
  lines.push('🆔 ' + (S.sessionId || ''));
  lines.push('🕐 Login ' + (S.loginTime ? (_hm(S.loginTime) + ' — ' + _dateStr(S.loginTime)) : '—'));
  return lines.join('\n');
}
function _buildReport(reasonLabel) {
  var S = _sessionAudit;
  var durStr = S.duration || _dur((S.logoutTime || Date.now()) - (S.loginTime || Date.now()));
  function apiCount(m) { return S.api[m].length; }
  var apiTotal = apiCount('GET') + apiCount('POST') + apiCount('PUT') + apiCount('PATCH') + apiCount('DELETE');
  var lines = [];
  lines.push(reasonLabel);
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('👤 ' + (S.username || 'Unknown user'));
  lines.push('🌐 ' + (S.environment || 'Unknown'));
  lines.push('🆔 ' + (S.sessionId || ''));
  lines.push('🕐 Login');
  lines.push(S.loginTime ? _hm(S.loginTime) : '—');
  lines.push('🕐 Logout');
  lines.push(S.logoutTime ? _hm(S.logoutTime) : '—');
  lines.push('⏱ Duration');
  lines.push(durStr);
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Modules Visited');
  lines.push(S.modulesVisited.length ? S.modulesVisited.map(function (m) { return '• ' + m; }).join('\n') : '—');
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Uploaded Files');
  lines.push(S.uploadedFiles.length ? S.uploadedFiles.join('\n') : '—');
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Downloads');
  lines.push('Templates : ' + S.downloads.templates);
  lines.push('Reports : ' + S.downloads.reports);
  lines.push('Data : ' + S.downloads.data);
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Database Operations');
  lines.push('Created : ' + S.dbOperations.created);
  lines.push('Updated : ' + S.dbOperations.updated);
  lines.push('Deleted : ' + S.dbOperations.deleted);
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('API Summary');
  lines.push('GET : ' + apiCount('GET'));
  lines.push('POST : ' + apiCount('POST'));
  lines.push('PUT : ' + apiCount('PUT'));
  lines.push('PATCH : ' + apiCount('PATCH'));
  lines.push('DELETE : ' + apiCount('DELETE'));
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Validation Errors');
  lines.push(String(S.validationErrors.length));
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('API Errors');
  lines.push(String(S.apiErrors.length));
  lines.push('━━━━━━━━━━━━━━━━━━━━━━');
  lines.push('Transactions');
  lines.push(String(S.transactions.length));
  if (apiTotal > 0) {
    lines.push('━━━━━━━━━━━━━━━━━━━━━━');
    lines.push('API DETAILS');
    ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].forEach(function (m) {
      S.api[m].forEach(function (entry) {
        lines.push(m + ' ' + entry.endpoint);
        lines.push(String(entry.status));
        lines.push(entry.elapsed + ' ms');
      });
    });
  }
  return lines.join('\n');
}
var Audit = {
  active: function () { return !!_sessionAudit.sessionId; },
  startSession: function (username, environment) {
    if (this.active()) return _sessionAudit.sessionId;
    _sessionAudit = _freshBuffer();
    _txnCounter = 0;
    _sessionAudit.sessionId = _genSID();
    _sessionAudit.username = (username && username.trim()) ? username.trim() : 'Unknown user';
    _sessionAudit.environment = environment || 'Unknown';
    _sessionAudit.loginTime = Date.now();
    // NEW: fire the immediate LOGIN webhook message right here, once
    // the buffer has real sessionId/username/environment/loginTime.
    // This is a SEPARATE send from the merged logout report below —
    // that one is unaffected and still fires only at endSession().
    _sendChunked(_buildLoginReport());
    return _sessionAudit.sessionId;
  },
  endSession: function (reason) {
    reason = reason || 'LOGOUT';
    if (!this.active()) return;
    _sessionAudit.logoutTime = Date.now();
    _sessionAudit.duration = _dur(_sessionAudit.logoutTime - _sessionAudit.loginTime);
    var icon = reason === 'TOKEN_EXPIRED' ? '⚠️ TOKEN EXPIRED' : reason === 'TIMEOUT' ? '⏳ SESSION TIMEOUT' : '🔴 LOGOUT';
    var report = _buildReport(icon);
    _sendChunked(report);
    _sessionAudit = _freshBuffer();
  },
  newTransaction: function () { return _genTxn(); },
  onModuleOpen: function (moduleName) {
    if (!this.active() || !moduleName) return;
    if (_sessionAudit.modulesVisited.indexOf(moduleName) === -1) _sessionAudit.modulesVisited.push(moduleName);
  },
  onModuleClose: function () {},
  onFileSelected: function (filename) {
    if (!this.active() || !filename) return;
    if (_sessionAudit.uploadedFiles.indexOf(filename) === -1) _sessionAudit.uploadedFiles.push(filename);
  },
  onDownload: function (filename) {
    if (!this.active() || !filename) return;
    var f = filename.toLowerCase();
    if (f.indexOf('template') !== -1) _sessionAudit.downloads.templates++;
    else if (f.indexOf('report') !== -1 || f.indexOf('success') !== -1 || f.indexOf('failed') !== -1) _sessionAudit.downloads.reports++;
    else _sessionAudit.downloads.data++;
  },
  onDbOp: function (kind, count) {
    count = count || 1;
    if (!this.active()) return;
    if (kind === 'created') _sessionAudit.dbOperations.created += count;
    else if (kind === 'updated') _sessionAudit.dbOperations.updated += count;
    else if (kind === 'deleted') _sessionAudit.dbOperations.deleted += count;
  },
  onValidationError: function (msg) {
    if (!this.active()) return;
    _sessionAudit.validationErrors.push(msg || 'Validation error');
  },
  onApiError: function (msg) {
    if (!this.active()) return;
    _sessionAudit.apiErrors.push(msg || 'API error');
  },
  onApiCall: function (evt) {
    if (!this.active()) return;
    var m = (evt.method || 'GET').toUpperCase();
    if (!_sessionAudit.api[m]) _sessionAudit.api[m] = [];
    _sessionAudit.api[m].push({ endpoint: evt.endpoint, status: evt.status, elapsed: evt.elapsed });
    if (evt.status && Number(evt.status) >= 400) this.onApiError(m + ' ' + evt.endpoint + ' → HTTP ' + evt.status);
  },
  getSessionSnapshot: function () { return JSON.parse(JSON.stringify(_sessionAudit)); }
};
function _shortEndpoint(url) {
  try {
    var u = new URL(url, window.location.origin);
    return u.pathname.replace(/^\/api/, '');
  } catch (e) {
    return String(url).split('?')[0];
  }
}
var ApiTracker = {
  fetch: function (url, options, moduleName) {
    options = options || {};
    var method = (options.method || 'GET').toUpperCase();
    var t0 = (window.performance && performance.now) ? performance.now() : Date.now();
    return fetch(url, options).then(function (res) {
      var elapsed = Math.round(((window.performance && performance.now) ? performance.now() : Date.now()) - t0);
      Audit.onApiCall({ method: method, endpoint: _shortEndpoint(url), status: res.status, elapsed: elapsed });
      if (res.status === 401 && url.indexOf('oauth/token') === -1) {
        Audit.endSession('TOKEN_EXPIRED');
      }
      return res;
    }, function (err) {
      var elapsed = Math.round(((window.performance && performance.now) ? performance.now() : Date.now()) - t0);
      Audit.onApiCall({ method: method, endpoint: _shortEndpoint(url), status: 'NET_ERR', elapsed: elapsed });
      throw err;
    });
  }
};
window.addEventListener('beforeunload', function () { try { Audit.endSession('LOGOUT'); } catch (e) {} });
window.addEventListener('unhandledrejection', function () { try { Audit.onApiError('Unhandled promise rejection'); } catch (e) {} });
AppCtx.Audit = Audit;
AppCtx.ApiTracker = ApiTracker;