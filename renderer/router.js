/* =========================================================
 * router.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Load order: AFTER common.js, BEFORE audit.js/notifications.js/login.js.
 * Because audit.js hasn't loaded yet when this file's top level runs,
 * Audit is referenced lazily (via AppCtx.Audit) inside go(), never at
 * the top of this file.
 * ========================================================= */
'use strict';

var BASE_SCREENS = ['screen-login', 'screen-hub'];
var ALL_SCREENS = BASE_SCREENS.slice();
var SCREEN_MODULE_MAP = {};
var _prevScreen = null;

function routerRegister() {
  for (var i = 0; i < arguments.length; i++) {
    var id = arguments[i];
    if (ALL_SCREENS.indexOf(id) === -1) ALL_SCREENS.push(id);
  }
}

function routerMapModule(rootScreenId, moduleName) {
  SCREEN_MODULE_MAP[rootScreenId] = moduleName;
}

function routerIsRoot(screenId) {
  return !!SCREEN_MODULE_MAP[screenId];
}

function routerGo(screenId) {
  ALL_SCREENS.forEach(function (s) {
    var el = document.getElementById(s);
    if (el) el.style.display = 'none';
  });
  var target = document.getElementById(screenId);
  if (target) target.style.display = 'block';

  var newMod = SCREEN_MODULE_MAP[screenId] || null;
  if (newMod && routerIsRoot(screenId) && AppCtx.Audit && typeof AppCtx.Audit.onModuleOpen === 'function') {
    AppCtx.Audit.onModuleOpen(newMod);
  }
  _prevScreen = screenId;
}

function routerCurrentScreen() { return _prevScreen; }

function routerWireDataGoLinks(root) {
  root = root || document;
  root.querySelectorAll('[data-go]').forEach(function (el) {
    el.onclick = function () { routerGo(el.getAttribute('data-go')); };
  });
}

AppCtx.Router = {
  ALL_SCREENS: ALL_SCREENS,
  register: routerRegister,
  mapModule: routerMapModule,
  isRoot: routerIsRoot,
  go: routerGo,
  currentScreen: routerCurrentScreen,
  wireDataGoLinks: routerWireDataGoLinks
};
