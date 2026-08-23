/* =========================================================
 * notifications.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * No dependencies on any other file. Owns EVERY user-facing
 * status/log/toast rendering — modules call these and never touch
 * a .bf-status / .bf-log element directly.
 *
 * CHANGE LOG (added: instant login toast):
 *   - NEW: Notifications.toast({ title, accent, rows, duration })
 *     renders a floating, auto-dismissing card (top-right) with a
 *     title row and a list of icon+text rows — used for the instant
 *     "you're logged in" confirmation. Purely additive; every
 *     existing method (status/success/error/warning/info/log/
 *     clearLog/progress/loading/doneLoading/alert) is byte-for-byte
 *     unchanged, so no existing module call site is affected.
 *   - Existing behavior note (not changed, just documented): status()
 *     overwrites the target element's className entirely
 *     ('bf-status show ' + type). styles.js has a hard override on
 *     #hub-meta specifically so this can't visually break the user
 *     badge — see styles.js comments.
 * ========================================================= */
'use strict';
function _nSetStatus(id, msg, type) {
  var el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = 'bf-status show ' + type;
}
function _nLog(containerId, msg, type) {
  type = type || 'info';
  var el = document.getElementById(containerId);
  if (!el) return;
  el.style.display = 'block';
  el.innerHTML += '<div class="' + type + '">' + msg + '</div>';
  el.scrollTop = el.scrollHeight;
}
function _nClearLog(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = '';
  el.style.display = 'none';
}

// ---------------------------------------------------------
// Toast layer — a small stack of floating cards, top-right.
// Independent of the .bf-status system above (different container,
// different lifecycle: auto-created, auto-dismissed, stackable).
// ---------------------------------------------------------
var _toastSeq = 0;
function _nToastHost() {
  var host = document.getElementById('bf-toast-host');
  if (!host) {
    host = document.createElement('div');
    host.id = 'bf-toast-host';
    // Appended to <body> (not the modal) so it always renders above
    // everything, including the full-window overlay.
    document.body.appendChild(host);
  }
  return host;
}
/**
 * Notifications.toast({ title, accent, rows, duration })
 *   title    — string, e.g. 'LOGIN'
 *   accent   — 'red' | 'green' | 'blue' | 'amber' (default 'blue')
 *   rows     — array of { icon: '👤', text: 'BTE362ONROLLADMIN' }
 *   duration — ms before auto-dismiss (default 6000; pass 0 to
 *              require manual close)
 * Returns the toast's DOM element (rarely needed by callers).
 */
function _nToast(opts) {
  opts = opts || {};
  var accent = opts.accent || 'blue';
  var duration = (opts.duration === undefined) ? 6000 : opts.duration;
  var rows = opts.rows || [];
  var host = _nToastHost();
  var id = 'bf-toast-' + (++_toastSeq);

  var card = document.createElement('div');
  card.id = id;
  card.className = 'bf-toast bf-toast-' + accent;

  var dotColors = { red: '🔴', green: '🟢', blue: '🔵', amber: '🟠' };
  var dot = dotColors[accent] || '🔵';

  var rowsHTML = rows.map(function (r) {
    return '<div class="bf-toast-row"><span class="bf-toast-row-icon">' + (r.icon || '') + '</span>' +
      '<span class="bf-toast-row-text">' + (r.text || '') + '</span></div>';
  }).join('');

  card.innerHTML =
    '<button class="bf-toast-close" type="button" aria-label="Dismiss">✕</button>' +
    '<div class="bf-toast-title">' + dot + ' ' + (opts.title || '') + '</div>' +
    '<div class="bf-toast-divider"></div>' +
    '<div class="bf-toast-rows">' + rowsHTML + '</div>';

  host.appendChild(card);
  // Force a reflow so the enter transition actually plays.
  void card.offsetWidth;
  card.classList.add('bf-toast-in');

  function dismiss() {
    card.classList.remove('bf-toast-in');
    card.classList.add('bf-toast-out');
    setTimeout(function () { if (card.parentNode) card.parentNode.removeChild(card); }, 220);
  }
  card.querySelector('.bf-toast-close').addEventListener('click', function (e) {
    e.stopPropagation();
    dismiss();
  });
  if (duration > 0) setTimeout(dismiss, duration);

  return card;
}

var Notifications = {
  status: function (id, msg, type) { _nSetStatus(id, msg, type); },
  success: function (id, msg) { _nSetStatus(id, msg, 'success'); },
  error: function (id, msg) { _nSetStatus(id, msg, 'error'); },
  warning: function (id, msg) { _nSetStatus(id, msg, 'info'); },
  info: function (id, msg) { _nSetStatus(id, msg, 'info'); },
  log: function (containerId, msg, type) { _nLog(containerId, msg, type); },
  clearLog: function (id) { _nClearLog(id); },
  progress: {
    show: function (progId) { var el = document.getElementById(progId); if (el) el.style.display = 'block'; },
    hide: function (progId, delay) {
      var el = document.getElementById(progId);
      if (!el) return;
      if (delay > 0) setTimeout(function () { el.style.display = 'none'; }, delay);
      else el.style.display = 'none';
    },
    set: function (barId, pct) {
      var el = document.getElementById(barId);
      if (el) el.style.width = Math.max(0, Math.min(100, Math.round(pct))) + '%';
    },
    done: function (barId, resetAfterMs) {
      resetAfterMs = (resetAfterMs === undefined) ? 2500 : resetAfterMs;
      var el = document.getElementById(barId);
      if (!el) return;
      el.classList.add('done');
      if (resetAfterMs > 0) {
        setTimeout(function () { el.classList.remove('done'); el.style.width = '0%'; }, resetAfterMs);
      }
    }
  },
  loading: function (btnEl, label) {
    if (!btnEl) return;
    btnEl.disabled = true;
    btnEl.innerHTML = '<span class="bf-spinner"></span> ' + label;
  },
  doneLoading: function (btnEl, label) {
    if (!btnEl) return;
    btnEl.disabled = false;
    btnEl.innerHTML = label;
  },
  alert: function (msg) { window.alert(msg); },
  toast: function (opts) { return _nToast(opts); }
};
AppCtx.Notifications = Notifications;