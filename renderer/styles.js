/* =========================================================
 * styles.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Do NOT wrap this file in function(AppCtx){...} — the loader already
 * builds that function for us; this file IS the function body.
 * No dependencies on any other file.
 *
 * CHANGE LOG (instant login toast):
 *   - NEW: #bf-toast-host + .bf-toast(-in/-out) + accent variants
 *     (red/green/blue/amber) + .bf-toast-title/-divider/-rows/-row/
 *     -row-icon/-row-text/-close. Renders the login confirmation card
 *     top-right, above the app shell (host is appended to <body> by
 *     notifications.js, not inside #bf-hub-modal, so it survives even
 *     if the modal is scrolled).
 *   - #hub-meta override kept as a permanent safeguard: confirmed
 *     against the real notifications.js that _nSetStatus() does
 *     el.className = 'bf-status show ' + type, which would otherwise
 *     turn #hub-meta into a large colored pill any time
 *     Notifications.status('hub-meta', ...) is called (e.g. from
 *     index.js's loadModule()).
 *   - Everything else — top bar, session card, module grid/sections,
 *     footer, module-screen container fix, button/action-card/
 *     breadcrumb styling — UNCHANGED.
 * ========================================================= */
'use strict';

var BF_HUB_CSS = [
  // ---- App shell (full window, not a floating card) ----
  '#bf-hub-overlay{position:fixed;inset:0;background:#F3F4F6;z-index:999999;',
  '  display:flex;align-items:stretch;justify-content:stretch;',
  '  font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Inter,sans-serif;}',
  '#bf-hub-modal{background:#F3F4F6;border-radius:0;padding:0;',
  '  width:100%;height:100%;max-width:100%;max-height:100%;overflow-y:auto;position:relative;box-sizing:border-box;}',
  '#bf-hub-modal > *{box-sizing:border-box;}',
  '.bf-shell-inner{max-width:1440px;margin:0 auto;padding:20px 28px 40px;}',

  // ---- Generic container for every module screen (screen-xxx),
  // excluding the two screens login.js lays out itself. ----
  '#bf-hub-modal > div[id^="screen-"]:not(#screen-login):not(#screen-hub){',
  '  padding:32px 36px 52px;max-width:760px;margin:0 auto;width:100%;background:#fff;min-height:100%;}',

  '.bf-close-btn{position:absolute;top:14px;right:16px;background:none;border:none;',
  '  font-size:20px;cursor:pointer;color:#9CA3AF;z-index:5;}',
  '.bf-close-btn:hover{color:#111827;}',

  // ---- Login screen: centered card ----
  '.bf-login-shell{display:flex;align-items:center;justify-content:center;',
  '  min-height:100vh;width:100%;background:#F3F4F6;padding:40px 20px;box-sizing:border-box;}',
  '.bf-login-card{width:100%;max-width:380px;background:#fff;border:1px solid #E5E7EB;',
  '  border-radius:12px;padding:32px 28px;box-shadow:0 1px 3px rgba(0,0,0,.06);}',
  '.bf-logo{text-align:center;font-size:30px;margin-bottom:6px;}',
  '.bf-main-title{text-align:center;font-size:19px;font-weight:700;color:#111827;margin-bottom:4px;}',
  '.bf-main-sub{text-align:center;font-size:13px;color:#6B7280;margin-bottom:16px;}',
  '.bf-env-toggle{display:flex;gap:6px;background:#F3F4F6;border-radius:10px;padding:4px;margin-bottom:20px;}',
  '.bf-env-btn{flex:1;padding:8px;border-radius:8px;border:none;background:transparent;',
  '  font-size:12px;font-weight:600;color:#6B7280;cursor:pointer;transition:all 0.2s;text-align:center;}',
  '.bf-env-btn.active{background:#fff;color:#1D4ED8;box-shadow:0 1px 3px rgba(0,0,0,0.1);}',
  '.bf-env-btn .env-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;}',
  '.bf-env-btn[data-env=production] .env-dot{background:#059669;}',
  '.bf-env-btn[data-env=uat] .env-dot{background:#D97706;}',

  '.bf-env-badge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:99px;margin-left:6px;}',
  '.bf-env-badge.prod{background:#D1FAE5;color:#065F46;}',
  '.bf-env-badge.uat{background:#FEF3C7;color:#92400E;}',
  '.bf-section-label{font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;',
  '  letter-spacing:.5px;margin-bottom:12px;padding-left:2px;}',
  '.bf-section-label-blue{color:#1D4ED8;} .bf-section-label-indigo{color:#4338CA;}',
  '.bf-section-label-red{color:#DC2626;} .bf-section-label-green{color:#059669;}',
  '.bf-section-label-purple{color:#7C3AED;} .bf-section-label-gray{color:#6B7280;}',

  // ---- Dashboard module cards ----
  '.bf-module-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin-bottom:4px;}',
  '.bf-module-card{display:flex;align-items:center;gap:12px;padding:14px 14px;border-radius:10px;',
  '  border:1px solid #E5E7EB;background:#fff;cursor:pointer;text-align:left;',
  '  transition:all 0.18s ease;box-shadow:0 1px 2px rgba(16,24,40,.03);}',
  '.bf-module-card:hover{border-color:#1D4ED8;box-shadow:0 6px 16px rgba(29,78,216,.12);transform:translateY(-2px);}',
  '.bf-module-card:hover .mc-arrow{opacity:1;transform:translateX(2px);}',
  '.mc-icon-badge{width:38px;height:38px;border-radius:9px;flex-shrink:0;font-size:17px;',
  '  display:flex;align-items:center;justify-content:center;}',
  '.mc-accent-blue{background:#DBEAFE;} .mc-accent-indigo{background:#E0E7FF;}',
  '.mc-accent-red{background:#FEE2E2;} .mc-accent-green{background:#D1FAE5;}',
  '.mc-accent-purple{background:#EDE9FE;} .mc-accent-gray{background:#F3F4F6;}',
  '.mc-body{flex:1;min-width:0;}',
  '.mc-name{font-size:13px;font-weight:700;color:#111827;line-height:1.3;}',
  '.mc-desc{font-size:11px;color:#6B7280;margin-top:2px;line-height:1.35;}',
  '.mc-arrow{color:#9CA3AF;font-size:14px;opacity:0;transition:all .15s ease;flex-shrink:0;}',

  '.bf-divider{border:none;border-top:1px solid #E5E7EB;margin:20px 0;}',

  // ---- Buttons ----
  '.bf-btn{width:100%;padding:12px 16px;border:none;border-radius:9px;font-size:13.5px;font-weight:700;',
  '  cursor:pointer;transition:all 0.16s ease;margin-bottom:10px;letter-spacing:.1px;}',
  '.bf-dash-topbar .bf-btn{width:auto;margin-bottom:0;padding:8px 14px;white-space:nowrap;font-size:12.5px;}',
  '.bf-primary{background:#1D4ED8;color:#fff;box-shadow:0 1px 2px rgba(29,78,216,.15);}',
  '.bf-primary:hover{background:#1e40af;transform:translateY(-1px);box-shadow:0 6px 16px rgba(29,78,216,.28);}',
  '.bf-success{background:#059669;color:#fff;box-shadow:0 1px 2px rgba(5,150,105,.15);}',
  '.bf-success:hover{background:#047857;transform:translateY(-1px);box-shadow:0 6px 16px rgba(5,150,105,.28);}',
  '.bf-danger{background:#DC2626;color:#fff;box-shadow:0 1px 2px rgba(220,38,38,.15);}',
  '.bf-danger:hover{background:#b91c1c;transform:translateY(-1px);box-shadow:0 6px 16px rgba(220,38,38,.28);}',
  '.bf-outline{background:#fff;color:#374151;border:1.5px solid #D1D5DB;box-shadow:none;}',
  '.bf-outline:hover{background:#F9FAFB;border-color:#9CA3AF;}',
  '.bf-btn:active{transform:translateY(0);}',
  '.bf-btn:disabled{opacity:.5;cursor:not-allowed;transform:none !important;box-shadow:none !important;}',

  '.bf-warn-box{background:#FFF7ED;border-left:4px solid #F97316;padding:12px 16px;',
  '  border-radius:0 9px 9px 0;font-size:12.5px;color:#7C2D12;margin-bottom:16px;line-height:1.5;}',
  '.bf-info-box{background:#F0F9FF;border-left:4px solid #0EA5E9;padding:12px 16px;',
  '  border-radius:0 9px 9px 0;font-size:12.5px;color:#0C4A6E;margin-bottom:16px;line-height:1.5;}',
  '.bf-status{padding:10px 14px;border-radius:9px;font-size:13px;margin-bottom:14px;display:none;font-weight:500;}',
  '.bf-status.show{display:block;animation:bfstatein 0.25s ease;}',
  '.bf-status.success{background:#D1FAE5;color:#065F46;border:1px solid #6EE7B7;}',
  '.bf-status.error{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;}',
  '.bf-status.info{background:#DBEAFE;color:#1E3A8A;border:1px solid #BFDBFE;}',
  '.bf-label{font-size:13px;font-weight:600;color:#374151;margin-bottom:5px;display:block;}',
  '#bf-hub-modal input[type=text],#bf-hub-modal input[type=password],',
  '#bf-hub-modal input[type=date],#bf-hub-modal textarea, #bf-hub-modal select{',
  '  width:100%;padding:9px 12px;border:1.5px solid #D1D5DB;border-radius:8px;font-size:13px;',
  '  box-sizing:border-box;outline:none;margin-bottom:12px;background:#fff;color:#111827;font-family:inherit;cursor:pointer;}',
  '#bf-hub-modal input:focus,#bf-hub-modal textarea:focus,#bf-hub-modal select:focus{border-color:#1D4ED8;',
  '  box-shadow:0 0 0 3px rgba(29,78,216,0.1);}',

  // ---- Action cards (module screens: Download/Upload/View/Delete grids) ----
  '.bf-action-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin-bottom:14px;}',
  '.bf-action-card{padding:20px 18px;border-radius:12px;border:1px solid #E5E7EB;',
  '  background:#fff;cursor:pointer;text-align:left;transition:all 0.18s ease;',
  '  box-shadow:0 1px 2px rgba(16,24,40,.04);}',
  '.bf-action-card:hover{border-color:#1D4ED8;box-shadow:0 8px 20px rgba(29,78,216,.12);transform:translateY(-2px);}',
  '.bf-action-card .ac-icon{width:40px;height:40px;border-radius:10px;background:#EFF6FF;',
  '  display:flex;align-items:center;justify-content:center;font-size:19px;margin-bottom:12px;}',
  '.bf-action-card .ac-name{font-size:13.5px;font-weight:700;color:#111827;margin-bottom:4px;}',
  '.bf-action-card .ac-desc{font-size:11.5px;color:#6B7280;line-height:1.45;}',

  '.bf-log{background:#F8FAFC;border:1px solid #E5E7EB;border-radius:8px;padding:10px 12px;',
  '  font-size:12px;max-height:170px;overflow-y:auto;margin-bottom:10px;font-family:monospace;display:none;}',
  '.bf-log .ok{color:#059669;} .bf-log .fail{color:#DC2626;} .bf-log .info{color:#1D4ED8;}',
  '.bf-progress{height:5px;background:#E5E7EB;border-radius:3px;margin-bottom:12px;overflow:hidden;display:none;}',
  '@keyframes bfshine{0%{background-position:-400px 0}100%{background-position:calc(400px + 100%) 0}}',
  '.bf-pb{height:100%;border-radius:3px;transition:width 0.4s ease;',
  '  background:linear-gradient(90deg,#1D4ED8 0%,#60A5FA 40%,#1D4ED8 80%);background-size:400px 100%;animation:bfshine 1.6s linear infinite;}',
  '.bf-pb.done{background:#059669;animation:none;}',

  '.bf-breadcrumb{display:flex;align-items:center;gap:6px;font-size:12px;color:#6B7280;',
  '  margin-bottom:20px;flex-wrap:wrap;}',
  '.bf-breadcrumb .bc-link{cursor:pointer;color:#1D4ED8;font-weight:500;} .bf-breadcrumb .bc-link:hover{text-decoration:underline;}',
  '.bf-breadcrumb .bc-sep{color:#D1D5DB;} .bf-breadcrumb .bc-cur{color:#111827;font-weight:600;}',
  '.bf-module-header{display:flex;align-items:center;gap:14px;margin-bottom:26px;',
  '  padding-bottom:20px;border-bottom:1px solid #E5E7EB;}',
  '.bf-module-header .mh-icon{font-size:22px;width:48px;height:48px;border-radius:12px;',
  '  background:#EFF6FF;display:flex;align-items:center;justify-content:center;flex-shrink:0;}',
  '.bf-module-header .mh-title{font-size:18px;font-weight:800;color:#111827;letter-spacing:-.2px;}',
  '.bf-module-header .mh-sub{font-size:12px;color:#6B7280;margin-top:3px;}',

  '.bf-spinner{display:inline-block;width:13px;height:13px;border:2px solid currentColor;',
  '  border-top-color:transparent;border-radius:50%;animation:bfhspin 0.6s linear infinite;',
  '  vertical-align:middle;margin-right:5px;}',
  '@keyframes bfhspin{to{transform:rotate(360deg);}}',

  '.bf-file-label{display:block;padding:26px 18px;border:2px dashed #CBD5E1;border-radius:12px;',
  '  text-align:center;cursor:pointer;color:#6B7280;font-size:13.5px;font-weight:500;',
  '  margin-bottom:14px;transition:all 0.18s ease;background:#FAFBFC;}',
  '.bf-file-label:hover{border-color:#1D4ED8;background:#EFF6FF;color:#1D4ED8;}',
  '.bf-file-input{display:none;}',
  '.bf-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}',
  '.bf-task-summary{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}',
  '@keyframes bfstatein{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}',
  '@keyframes bfpopIn{from{opacity:0;transform:scale(.98)}to{opacity:1;transform:scale(1)}}',
  '#bf-hub-modal{animation:bfpopIn 0.18s ease;}',
  '.bf-task-chip{padding:5px 12px;border-radius:99px;font-size:12px;font-weight:600;',
  '  background:#EFF6FF;color:#1E3A8A;border:1px solid #BFDBFE;}',
  '.bf-file-info{align-items:center;gap:10px;padding:10px 14px;background:#F0F9FF;',
  '  border:1.5px solid #BAE6FD;border-radius:8px;margin-bottom:10px;}',
  '.bf-file-info .fi-name{font-size:13px;font-weight:600;color:#0C4A6E;flex:1;',
  '  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',
  '.bf-remove-btn{background:none;border:1.5px solid #FECACA;border-radius:6px;padding:4px 10px;',
  '  font-size:12px;font-weight:600;color:#991B1B;cursor:pointer;white-space:nowrap;flex-shrink:0;}',
  '.bf-remove-btn:hover{background:#FEE2E2;}',
  '.pun-dir-toggle{display:flex;gap:6px;background:#F3F4F6;border-radius:10px;padding:4px;margin-bottom:14px;}',
  '.pun-dir-btn{flex:1;padding:8px;border-radius:8px;border:none;background:transparent;font-size:12px;font-weight:600;color:#6B7280;cursor:pointer;transition:all 0.2s;}',
  '.pun-dir-btn.active{background:#fff;color:#1D4ED8;box-shadow:0 1px 3px rgba(0,0,0,0.1);}',

  // ---- Top-bar dashboard shell ----
  '.bf-dash{display:flex;flex-direction:column;width:100%;min-height:100vh;}',
  '.bf-dash-topbar{display:flex;align-items:center;justify-content:space-between;',
  '  padding:12px 28px;background:#fff;border-bottom:1px solid #E5E7EB;',
  '  flex-shrink:0;gap:16px;flex-wrap:wrap;position:sticky;top:0;z-index:3;}',
  '.bf-dash-brand{display:flex;align-items:center;gap:8px;}',
  '.bf-dash-logo{font-size:22px;}',
  '.bf-dash-brand-name{font-size:16px;font-weight:800;color:#111827;letter-spacing:-.2px;}',
  '.bf-dash-topbar-right{display:flex;align-items:center;gap:12px;flex-wrap:wrap;}',

  '.bf-chip{display:flex;align-items:center;gap:8px;padding:6px 12px;border:1px solid #E5E7EB;',
  '  border-radius:9px;background:#F9FAFB;}',
  '.bf-chip-label{font-size:9px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#9CA3AF;}',
  '.bf-chip-value{font-size:12px;font-weight:600;color:#1D4ED8;}',
  '.bf-env-pill{font-size:10px;font-weight:800;letter-spacing:.03em;padding:2px 9px;border-radius:99px;}',
  '.bf-env-pill-prod{background:#D1FAE5;color:#065F46;}',
  '.bf-env-pill-uat{background:#FEF3C7;color:#92400E;}',
  '.bf-chip-conn{gap:8px;}',
  '.bf-conn-dot{width:8px;height:8px;border-radius:50%;background:#059669;flex-shrink:0;',
  '  box-shadow:0 0 0 3px rgba(5,150,105,.15);}',

  '.bf-user-badge{display:flex;align-items:center;gap:10px;background:#EFF6FF;',
  '  border-radius:10px;padding:6px 12px;min-width:0;}',
  '.bf-user-avatar{width:32px;height:32px;border-radius:50%;background:#1D4ED8;color:#fff;',
  '  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;}',
  '.bf-user-name{font-size:12.5px;font-weight:700;color:#1E3A8A;white-space:nowrap;}',
  '.bf-user-meta{font-size:10.5px;color:#3B82F6;white-space:nowrap;}',

  // ---- FIX: #hub-meta is dynamically restyled by
  // Notifications.status('hub-meta', ...) (confirmed: _nSetStatus()
  // does el.className = 'bf-status show ' + type). This override
  // forces #hub-meta to always render as small, contained badge
  // text no matter which classes get applied to it at runtime. ----
  '#hub-meta{font-size:10.5px !important;font-weight:500 !important;color:#3B82F6 !important;',
  '  background:none !important;border:none !important;padding:0 !important;margin:0 !important;',
  '  display:block !important;white-space:nowrap !important;overflow:hidden !important;',
  '  text-overflow:ellipsis !important;max-width:180px !important;border-radius:0 !important;',
  '  box-shadow:none !important;animation:none !important;}',

  '.bf-main-scroll{flex:1;}',

  '.bf-session-card{background:#fff;border:1px solid #E5E7EB;border-radius:14px;',
  '  padding:18px 22px;margin-bottom:22px;box-shadow:0 1px 2px rgba(16,24,40,.03);}',
  '.bf-session-title{font-size:12px;font-weight:700;color:#1D4ED8;margin-bottom:12px;}',
  '.bf-session-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px 22px;}',
  '.bf-session-row{display:flex;justify-content:space-between;gap:10px;font-size:12px;',
  '  padding:6px 0;border-bottom:1px dashed #F3F4F6;}',
  '.bf-session-row span{color:#9CA3AF;}',
  '.bf-session-row b{color:#111827;font-weight:600;text-align:right;}',

  '.bf-module-section{margin-bottom:26px;}',
  '#hub-module-sections{margin-top:4px;}',

  '.bf-dash-footer{display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between;',
  '  align-items:flex-start;background:#F3F4F6;border:1px solid #E5E7EB;border-radius:14px;',
  '  padding:18px 24px;margin-top:8px;font-size:11.5px;color:#6B7280;}',
  '.bf-footer-item{display:flex;align-items:flex-start;gap:10px;}',
  '.bf-footer-item b{color:#111827;font-size:12.5px;}',
  '.bf-footer-icon{font-size:16px;flex-shrink:0;}',
  '.bf-footer-item-right{margin-left:auto;}',

  // ---- Login toast (top-right, floating, independent of #bf-hub-modal) ----
  '#bf-toast-host{position:fixed;top:20px;right:20px;z-index:2147483647;',
  '  display:flex;flex-direction:column;gap:10px;',
  '  font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Inter,sans-serif;',
  '  pointer-events:none;}',
  '.bf-toast{pointer-events:auto;position:relative;width:300px;background:#fff;',
  '  border-radius:12px;padding:16px 18px 14px;box-shadow:0 12px 32px rgba(15,23,42,.18);',
  '  border-left:4px solid #1D4ED8;opacity:0;transform:translateX(24px) scale(.98);',
  '  transition:opacity .2s ease,transform .2s ease;}',
  '.bf-toast-red{border-left-color:#DC2626;}',
  '.bf-toast-green{border-left-color:#059669;}',
  '.bf-toast-blue{border-left-color:#1D4ED8;}',
  '.bf-toast-amber{border-left-color:#D97706;}',
  '.bf-toast-in{opacity:1;transform:translateX(0) scale(1);}',
  '.bf-toast-out{opacity:0;transform:translateX(24px) scale(.98);}',
  '.bf-toast-close{position:absolute;top:10px;right:10px;background:none;border:none;',
  '  color:#9CA3AF;font-size:13px;cursor:pointer;line-height:1;padding:2px;}',
  '.bf-toast-close:hover{color:#111827;}',
  '.bf-toast-title{font-size:12.5px;font-weight:800;letter-spacing:.04em;color:#111827;',
  '  padding-right:18px;}',
  '.bf-toast-divider{border-top:1px dashed #E5E7EB;margin:8px 0 10px;}',
  '.bf-toast-rows{display:flex;flex-direction:column;gap:6px;}',
  '.bf-toast-row{display:flex;align-items:center;gap:8px;font-size:12.5px;color:#374151;}',
  '.bf-toast-row-icon{flex-shrink:0;width:16px;text-align:center;}',
  '.bf-toast-row-text{font-weight:600;color:#111827;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}',

  // ---- Small screens: never allow horizontal scroll ----
  '@media (max-width:900px){',
  '  .bf-dash-topbar{padding:12px 16px;}',
  '  .bf-shell-inner{padding:14px 16px 32px;}',
  '  .bf-module-grid{grid-template-columns:1fr;}',
  '  .bf-action-grid{grid-template-columns:1fr;}',
  '  .bf-dash-footer{flex-direction:column;}',
  '  .bf-footer-item-right{margin-left:0;}',
  '  #bf-hub-modal > div[id^="screen-"]:not(#screen-login):not(#screen-hub){padding:22px 18px 36px;}',
  '  #hub-meta{max-width:110px !important;}',
  '  #bf-toast-host{top:12px;right:12px;left:12px;}',
  '  .bf-toast{width:100%;}',
  '}',
  '@media (max-width:560px){',
  '  .bf-dash-topbar{flex-direction:column;align-items:flex-start;}',
  '  .bf-dash-topbar-right{width:100%;justify-content:flex-start;}',
  '}'
].join('\n');

function injectStyles() {
  var existing = document.getElementById('bf-hub-style');
  if (existing) return existing;
  var style = document.createElement('style');
  style.id = 'bf-hub-style';
  style.textContent = BF_HUB_CSS;
  document.head.appendChild(style);
  return style;
}

function removeStyles() {
  var el = document.getElementById('bf-hub-style');
  if (el) el.remove();
  var host = document.getElementById('bf-toast-host');
  if (host) host.remove();
}

// Inject immediately — styles.js has zero dependencies.
injectStyles();

AppCtx.Styles = { injectStyles: injectStyles, removeStyles: removeStyles, CSS: BF_HUB_CSS };