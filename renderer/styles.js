/* =========================================================
 * styles.js — BeeForce Configuration Portal
 * Plain script body. Executed as: new Function('AppCtx', <this file>)
 * Do NOT wrap this file in function(AppCtx){...} — the loader already
 * builds that function for us; this file IS the function body.
 * No dependencies on any other file.
 * ========================================================= */
'use strict';

var BF_HUB_CSS = [
  '#bf-hub-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:999999;',
  '  display:flex;align-items:center;justify-content:center;',
  '  font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;}',
  '#bf-hub-modal{background:#fff;border-radius:16px;padding:26px 24px;',
  '  width:600px;max-width:96vw;max-height:92vh;overflow-y:auto;position:relative;}',
  '.bf-close-btn{position:absolute;top:14px;right:16px;background:none;border:none;',
  '  font-size:20px;cursor:pointer;color:#9CA3AF;}',
  '.bf-close-btn:hover{color:#111827;}',
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
  '.bf-user-badge{display:flex;align-items:center;gap:10px;background:#EFF6FF;',
  '  border-radius:10px;padding:10px 14px;margin-bottom:18px;}',
  '.bf-user-avatar{width:34px;height:34px;border-radius:50%;background:#1D4ED8;color:#fff;',
  '  display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;}',
  '.bf-user-name{font-size:13px;font-weight:600;color:#1E3A8A;}',
  '.bf-user-meta{font-size:11px;color:#3B82F6;}',
  '.bf-env-badge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:99px;margin-left:6px;}',
  '.bf-env-badge.prod{background:#D1FAE5;color:#065F46;}',
  '.bf-env-badge.uat{background:#FEF3C7;color:#92400E;}',
  '.bf-section-label{font-size:11px;font-weight:600;color:#9CA3AF;text-transform:uppercase;',
  '  letter-spacing:.5px;margin-bottom:10px;}',
  '.bf-module-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:9px;margin-bottom:4px;}',
  '.bf-module-card{padding:13px 8px;border-radius:10px;border:1.5px solid #E5E7EB;',
  '  background:#F9FAFB;cursor:pointer;text-align:center;transition:all 0.22s cubic-bezier(.34,1.56,.64,1);}',
  '.bf-module-card:hover{border-color:#1D4ED8;background:#EFF6FF;transform:translateY(-3px);box-shadow:0 6px 18px rgba(29,78,216,.14);}',
  '.bf-module-card .mc-icon{font-size:20px;margin-bottom:5px;}',
  '.bf-module-card .mc-name{font-size:11px;font-weight:600;color:#111827;line-height:1.3;}',
  '.bf-divider{border:none;border-top:1px solid #E5E7EB;margin:16px 0;}',
  '.bf-btn{width:100%;padding:10px;border:none;border-radius:8px;font-size:13px;font-weight:600;',
  '  cursor:pointer;transition:all 0.18s ease;margin-bottom:8px;}',
  '.bf-primary{background:#1D4ED8;color:#fff;} .bf-primary:hover{background:#1e40af;transform:translateY(-1px);box-shadow:0 3px 10px rgba(29,78,216,.25);}',
  '.bf-success{background:#059669;color:#fff;} .bf-success:hover{background:#047857;transform:translateY(-1px);box-shadow:0 3px 10px rgba(5,150,105,.25);}',
  '.bf-danger{background:#DC2626;color:#fff;}  .bf-danger:hover{background:#b91c1c;transform:translateY(-1px);box-shadow:0 3px 10px rgba(220,38,38,.25);}',
  '.bf-outline{background:#fff;color:#374151;border:1.5px solid #D1D5DB;}',
  '.bf-outline:hover{background:#F9FAFB;}',
  '.bf-warn-box{background:#FFF7ED;border-left:4px solid #F97316;padding:10px 14px;',
  '  border-radius:0 8px 8px 0;font-size:12px;color:#7C2D12;margin-bottom:14px;}',
  '.bf-info-box{background:#F0F9FF;border-left:4px solid #0EA5E9;padding:10px 14px;',
  '  border-radius:0 8px 8px 0;font-size:12px;color:#0C4A6E;margin-bottom:14px;}',
  '.bf-status{padding:9px 13px;border-radius:8px;font-size:13px;margin-bottom:12px;display:none;}',
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
  '.bf-action-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;}',
  '.bf-action-card{padding:13px 10px;border-radius:10px;border:1.5px solid #E5E7EB;',
  '  background:#F9FAFB;cursor:pointer;text-align:center;transition:all 0.2s cubic-bezier(.34,1.56,.64,1);}',
  '.bf-action-card:hover{border-color:#1D4ED8;background:#EFF6FF;transform:translateY(-2px);box-shadow:0 4px 12px rgba(29,78,216,.12);}',
  '.bf-action-card .ac-icon{font-size:20px;margin-bottom:5px;}',
  '.bf-action-card .ac-name{font-size:12px;font-weight:600;color:#111827;}',
  '.bf-action-card .ac-desc{font-size:10px;color:#6B7280;margin-top:2px;}',
  '.bf-log{background:#F8FAFC;border:1px solid #E5E7EB;border-radius:8px;padding:10px 12px;',
  '  font-size:12px;max-height:170px;overflow-y:auto;margin-bottom:10px;font-family:monospace;display:none;}',
  '.bf-log .ok{color:#059669;} .bf-log .fail{color:#DC2626;} .bf-log .info{color:#1D4ED8;}',
  '.bf-progress{height:5px;background:#E5E7EB;border-radius:3px;margin-bottom:12px;overflow:hidden;display:none;}',
  '@keyframes bfshine{0%{background-position:-400px 0}100%{background-position:calc(400px + 100%) 0}}',
  '.bf-pb{height:100%;border-radius:3px;transition:width 0.4s ease;',
  '  background:linear-gradient(90deg,#1D4ED8 0%,#60A5FA 40%,#1D4ED8 80%);background-size:400px 100%;animation:bfshine 1.6s linear infinite;}',
  '.bf-pb.done{background:#059669;animation:none;}',
  '.bf-breadcrumb{display:flex;align-items:center;gap:6px;font-size:12px;color:#6B7280;',
  '  margin-bottom:14px;flex-wrap:wrap;}',
  '.bf-breadcrumb .bc-link{cursor:pointer;color:#1D4ED8;} .bf-breadcrumb .bc-link:hover{text-decoration:underline;}',
  '.bf-breadcrumb .bc-sep{color:#D1D5DB;} .bf-breadcrumb .bc-cur{color:#111827;font-weight:600;}',
  '.bf-module-header{display:flex;align-items:center;gap:10px;margin-bottom:14px;',
  '  padding-bottom:10px;border-bottom:1px solid #E5E7EB;}',
  '.bf-module-header .mh-icon{font-size:22px;}',
  '.bf-module-header .mh-title{font-size:15px;font-weight:700;color:#111827;}',
  '.bf-module-header .mh-sub{font-size:11px;color:#6B7280;margin-top:2px;}',
  '.bf-spinner{display:inline-block;width:13px;height:13px;border:2px solid currentColor;',
  '  border-top-color:transparent;border-radius:50%;animation:bfhspin 0.6s linear infinite;',
  '  vertical-align:middle;margin-right:5px;}',
  '@keyframes bfhspin{to{transform:rotate(360deg);}}',
  '.bf-file-label{display:block;padding:18px;border:2px dashed #D1D5DB;border-radius:10px;',
  '  text-align:center;cursor:pointer;color:#6B7280;font-size:13px;margin-bottom:12px;transition:all 0.2s;}',
  '.bf-file-label:hover{border-color:#1D4ED8;background:#EFF6FF;color:#1D4ED8;}',
  '.bf-file-input{display:none;}',
  '.bf-grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}',
  '.bf-task-summary{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}',
  '@keyframes bfstatein{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}',
  '@keyframes bfpopIn{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}',
  '#bf-hub-modal{animation:bfpopIn 0.22s ease;}',
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
  '.pun-dir-btn.active{background:#fff;color:#1D4ED8;box-shadow:0 1px 3px rgba(0,0,0,0.1);}'
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
}

// Inject immediately — styles.js has zero dependencies.
injectStyles();

AppCtx.Styles = { injectStyles: injectStyles, removeStyles: removeStyles, CSS: BF_HUB_CSS };
