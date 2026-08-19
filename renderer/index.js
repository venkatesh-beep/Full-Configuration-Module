/* =========================================================
 * BeeForce Configuration Portal — index.js
 * Plain JavaScript. NO import/export/module syntax anywhere.
 * Loaded by loader.js via: (0, eval)(code)
 * Everything below runs in the global scope that loader.js
 * evaluated it in, so `var` declarations here are visible to
 * every core file we go on to fetch + new Function(...).
 * ========================================================= */
(function () {
  'use strict';

  // ── Guard: re-clicking the bookmark ALWAYS forces a genuinely fresh
  // reload instead of re-showing whatever was already in the page. The
  // old version here just re-displayed the existing overlay, which meant
  // it kept running whatever core/module code was fetched the FIRST time
  // this session — even after you'd updated the gist. That caused a long
  // string of confusing "I updated the file but nothing changed" bugs.
  // Removing the stale overlay and falling through to a full re-init
  // means every click is guaranteed to pull the current gist content.
  var _existingOverlay = document.getElementById('bf-hub-overlay');
  if (_existingOverlay) { _existingOverlay.remove(); }

  // ── Single source of truth for the Gist location ────────
  // loader.js hands us BF_BASE / BF_LOADER_VERSION; fall back to a
  // literal here so index.js also works if fetched/eval'd directly.
  var BASE = (typeof BF_BASE !== 'undefined' && BF_BASE)
    ? BF_BASE
    : 'https://gist.githubusercontent.com/venkatesh-beep/fa5ed8674157d1bc89ec7ad74d8d2ff1/raw/';
  var LOADER_VERSION = (typeof BF_LOADER_VERSION !== 'undefined') ? BF_LOADER_VERSION : '2.0';

  // ── Build every file URL from ONE base — nothing else to edit ──
  var FILES = [
    'styles', 'common', 'notifications', 'router', 'audit', 'notifications', 'login'
  ];
  var MODULE_REGISTRY = [
    { id: 'timecard-update',        icon: '🕐', name: 'Timecard Update',       screen: 'screen-tc' },
    { id: 'ot-approval',            icon: '⏱️', name: 'OT Approval',           screen: 'screen-ota' },
    { id: 'workflow-transfer',      icon: '🔄', name: 'Workflow Transfer',     screen: 'screen-wft' },
    { id: 'punch',                  icon: '👊', name: 'Punch',                 screen: 'screen-pun' },
    { id: 'tasks',                  icon: '✅', name: 'Tasks',                 screen: 'screen-tasks' },
    { id: 'employee-lookup',        icon: '👤', name: 'Emp Lookup',            screen: 'screen-el' },
    { id: 'org-lookup',             icon: '🏢', name: 'Org Lookup',            screen: 'screen-ol' },
    { id: 'paycodes',               icon: '🎯', name: 'Paycodes',              screen: 'screen-pay' },
    { id: 'paycode-events',         icon: '📊', name: 'Paycode Events',        screen: 'screen-pe' },
    { id: 'paycode-event-sets',     icon: '🗂️', name: 'Event Sets',            screen: 'screen-pes' },
    { id: 'paycode-combinations',   icon: '🔗', name: 'Combinations',          screen: 'screen-pco' },
    { id: 'shift-templates',        icon: '📅', name: 'Shift Templates',       screen: 'screen-st' },
    { id: 'shift-template-sets',    icon: '📋', name: 'Shift Template Set',    screen: 'screen-sts' },
    { id: 'accrual',                icon: '🏦', name: 'Accrual',               screen: 'screen-accrual' },
    { id: 'accrual-policies',       icon: '📜', name: 'Accrual Policies',      screen: 'screen-accrpol' },
    { id: 'accrual-policy-sets',    icon: '📑', name: 'Accrual Policy Set',    screen: 'screen-aps' },
    { id: 'timeoff-policy-sets',    icon: '🏖️', name: 'Time Off Policy Set',   screen: 'screen-tops' },
    { id: 'timeoff-policy-config',  icon: '⚙️', name: 'Timeoff Policy Config', screen: 'screen-topolcfg' },
    { id: 'roles',                  icon: '🔑', name: 'Roles & Positions',     screen: 'screen-rol' },
    { id: 'accrual-balances',       icon: '📊', name: 'Accrual Balances',      screen: 'screen-acgr' },
    { id: 'timeoff-raise',          icon: '🙋', name: 'Timeoff Raise',         screen: 'screen-tor' },
    { id: 'regularization-policies',     icon: '📐', name: 'Regularization Policies',     screen: 'screen-regpol' },
    { id: 'regularization-policy-sets',  icon: '📐', name: 'Regularization Policy Set',   screen: 'screen-regpolset' },
    { id: 'outpass-policies',            icon: '🚪', name: 'Outpass Policies',            screen: 'screen-outpol' },
    { id: 'outpass-policy-sets',         icon: '🚪', name: 'Outpass Policy Set',          screen: 'screen-outpolset' }
  ];

  function gistUrl(name) { return BASE + name + '.js'; }
  function cacheBust(url) { return url + (url.indexOf('?') === -1 ? '?' : '&') + 't=' + Date.now(); }

  // ── Fetch + promise caches — a file is only ever downloaded once ──
  var _fetchCache = {};   // name -> Promise<string> (raw code)
  var _loadedCore = {};   // name -> true once its IIFE has executed
  var _loadedModule = {}; // moduleId -> true once init() has run
  var _loadQueue = Promise.resolve(); // serializes core loads in order

function fetchCode(name) {

    if (_fetchCache[name]) {
        return _fetchCache[name];
    }

    // ---------------------------------------------------------
    // Electron mode
    // ---------------------------------------------------------
    //
    // Load JavaScript directly from the local renderer folder.
    // No Gist and no network request.
    //
    if (
        typeof BF_IS_DESKTOP !== 'undefined' &&
        BF_IS_DESKTOP &&
        typeof BF_LOAD_LOCAL_FILE === 'function'
    ) {

        _fetchCache[name] =
            BF_LOAD_LOCAL_FILE(
                name + '.js'
            ).then(function (result) {

                if (
                    !result ||
                    !result.ok
                ) {

                    throw new Error(
                        'Local file not available: ' +
                        name +
                        '.js' +
                        (
                            result &&
                            result.error
                                ? ' (' + result.error + ')'
                                : ''
                        )
                    );
                }

                return result.content;
            });

        return _fetchCache[name];
    }

    // ---------------------------------------------------------
    // Hosted/browser mode
    // ---------------------------------------------------------
    //
    // Keep the existing Gist behavior for the hosted version.
    //
    var url =
        cacheBust(
            gistUrl(name)
        );

    _fetchCache[name] =
        fetch(url).then(function (r) {

            if (!r.ok) {

                throw new Error(
                    'HTTP ' +
                    r.status +
                    ' fetching ' +
                    name +
                    '.js'
                );
            }

            return r.text();
        });

    return _fetchCache[name];
}

  function logStep(msg, color) { console.log('%c' + msg, 'color:' + (color || '#6B7280') + ';'); }

  function reportError(fileLabel, url, err) {
    console.error('%c[BF] Failed loading ' + fileLabel, 'color:#DC2626;font-weight:bold;font-size:13px;');
    console.error('URL:', url);
    console.error('Message:', err.message);
    if (err.stack) console.error('Stack:', err.stack);
    setLoadStatus('❌ Failed: ' + fileLabel + ' — ' + err.message);
  }

  // ── Overlay shell (shown immediately, before any core file loads) ──
  var overlay = document.createElement('div');
  overlay.id = 'bf-hub-overlay';
  overlay.style.cssText = [
    'position:fixed', 'top:0', 'left:0', 'width:100%', 'height:100%',
    'background:rgba(17,24,39,0.55)', 'display:flex',
    'align-items:center', 'justify-content:center', 'z-index:2147483647',
    'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif'
  ].join(';');

  var modal = document.createElement('div');
  modal.id = 'bf-hub-modal';
  modal.style.cssText = [
    'background:#fff', 'border-radius:16px', 'width:600px', 'max-width:96vw', 'max-height:92vh',
    'overflow-y:auto', 'padding:26px 24px', 'position:relative'
  ].join(';');

  modal.innerHTML =
    '<div id="bf-loading-screen" style="text-align:center;padding:40px 20px;">' +
      '<div style="font-size:28px;margin-bottom:12px;">🐝</div>' +
      '<div style="font-size:16px;font-weight:700;color:#1D4ED8;margin-bottom:8px;">BeeForce Configuration Portal</div>' +
      '<div style="font-size:13px;color:#6B7280;" id="bf-load-status">Initialising… (loader v' + LOADER_VERSION + ')</div>' +
    '</div>';

  overlay.appendChild(modal);
  overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.style.display = 'none'; });
  document.body.appendChild(overlay);

  function setLoadStatus(msg) {
    var el = document.getElementById('bf-load-status');
    if (el) el.textContent = msg;
  }

  function showFatalError(fileLabel, url, err) {
    modal.innerHTML =
      '<div style="padding:24px;">' +
        '<div style="font-size:24px;margin-bottom:12px;text-align:center;">⚠️</div>' +
        '<div style="font-size:14px;font-weight:700;color:#DC2626;margin-bottom:8px;text-align:center;">Failed loading ' + fileLabel + '</div>' +
        '<div style="font-size:12px;color:#374151;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:10px;margin-bottom:8px;word-break:break-all;">' + (err.message || String(err)) + '</div>' +
        '<div style="font-size:11px;color:#9CA3AF;word-break:break-all;">URL: ' + url + '</div>' +
        '<div style="font-size:11px;color:#9CA3AF;margin-top:8px;">Check the file for import/export syntax or a syntax error, then reload.</div>' +
      '</div>';
  }

  // ── Application context — the ONLY thing every file receives ────
  // No imports. No exports. No globals beyond this single object.
  var AppCtx = {};
  AppCtx.modal = modal;
  AppCtx.overlay = overlay;
  AppCtx.BASE = BASE;
  AppCtx.LOADER_VERSION = LOADER_VERSION;
  AppCtx.MODULE_REGISTRY = MODULE_REGISTRY;

  // ── Core loader: fetch → new Function('AppCtx', code) → run ─────
  function loadCore(name) {
    if (_loadedCore[name]) return Promise.resolve();
    logStep('Loading ' + name + '.js…');
    setLoadStatus('Loading ' + name + '.js…');
    return fetchCode(name).then(function (code) {
      try {
        var fn = new Function('AppCtx', code);
        fn(AppCtx);
        _loadedCore[name] = true;
        logStep('✓ ' + name + '.js', '#059669');
      } catch (err) {
        var url = cacheBust(gistUrl(name));
        reportError(name + '.js', url, err);
        showFatalError(name + '.js', url, err);
        throw err;
      }
    }, function (err) {
      var url = err.bfUrl || cacheBust(gistUrl(name));
      reportError(name + '.js', url, err);
      showFatalError(name + '.js', url, err);
      throw err;
    });
  }

  // ── Lazy module loader — called when a hub card is clicked ──────
  // Modules define a top-level `function init(AppCtx){...}` and
  // nothing else; we append `return init(AppCtx);` ourselves so the
  // module file never needs any export/module syntax.
  AppCtx.loadModule = function (moduleId) {
    if (_loadedModule[moduleId]) return Promise.resolve();
    var entry = MODULE_REGISTRY.filter(function (m) { return m.id === moduleId; })[0];
    if (!entry) return Promise.reject(new Error('Unknown module: ' + moduleId));

    logStep('Loading module ' + moduleId + '.js…');
    if (AppCtx.Notifications) AppCtx.Notifications.status('hub-meta', 'Loading ' + entry.name + '...', 'info');

    return fetchCode(moduleId).then(function (code) {
      try {
        var factory = new Function('AppCtx', code + '\nreturn (typeof init === "function") ? init(AppCtx) : undefined;');
        factory(AppCtx);
        _loadedModule[moduleId] = true;
        if (AppCtx.Router) AppCtx.Router.mapModule(entry.screen, entry.name);
        logStep('✓ ' + moduleId + '.js', '#059669');
      } catch (err) {
        var url = cacheBust(gistUrl(moduleId));
        reportError(moduleId + '.js', url, err);
        if (AppCtx.Notifications) AppCtx.Notifications.status('hub-meta', '❌ Failed to load ' + entry.name, 'error');
        throw err;
      }
    }, function (err) {
      var url = err.bfUrl || cacheBust(gistUrl(moduleId));
      reportError(moduleId + '.js', url, err);
      if (AppCtx.Notifications) AppCtx.Notifications.status('hub-meta', '❌ Failed to load ' + entry.name, 'error');
      throw err;
    });
  };

  AppCtx.openModule = function (moduleId) {
    var entry = MODULE_REGISTRY.filter(function (m) { return m.id === moduleId; })[0];
    if (!entry) return;
    AppCtx.loadModule(moduleId).then(function () {
      AppCtx.Router.go(entry.screen);
    }).catch(function () { /* error already surfaced above */ });
  };

  // ── Wire module card clicks (cards are rendered by login.js) ────
  AppCtx.wireModuleCards = function () {
    var cards = modal.querySelectorAll('.bf-module-card');
    for (var i = 0; i < cards.length; i++) {
      (function (card) {
        var id = card.getAttribute('data-module');
        card.onclick = function () { AppCtx.openModule(id); };
      })(cards[i]);
    }
  };

  // ── Load core files strictly in order, then hand off to Login ───
  FILES.reduce(function (chain, name) {
    return chain.then(function () { return loadCore(name); });
  }, _loadQueue).then(function () {
    var loadingScreen = document.getElementById('bf-loading-screen');
    if (loadingScreen) loadingScreen.remove();

    // login.js is expected to expose AppCtx.Login = { init, logout, isTokenValid }
    // and to render both the login screen and the hub screen (module grid)
    // using AppCtx.MODULE_REGISTRY.
    if (AppCtx.Login && typeof AppCtx.Login.init === 'function') {
      AppCtx.Login.init();
      AppCtx.wireModuleCards();
    }

    logStep('BeeForce Ready', '#059669');
  }).catch(function (err) {
    // Already reported + rendered by loadCore's own error path.
    console.error('%c[BF] Bootstrap aborted.', 'color:#DC2626;font-weight:bold;');
  });

  // ── Page-unload audit flush ───────────────────────────────────
  window.addEventListener('beforeunload', function () {
    try { if (AppCtx.Audit) AppCtx.Audit.endSession('LOGOUT'); } catch (e) {}
  });

  // Expose for debugging in the console (not used by any module logic).
  window.__BF_APPCTX__ = AppCtx;
})();