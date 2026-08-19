/* =========================================================
 * notifications.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * No dependencies on any other file. Owns EVERY user-facing
 * status/log/toast rendering — modules call these and never touch
 * a .bf-status / .bf-log element directly.
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

  alert: function (msg) { window.alert(msg); }
};

AppCtx.Notifications = Notifications;
