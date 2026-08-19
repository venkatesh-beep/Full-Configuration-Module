/* =========================================================
 * workflow-transfer.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/workflow-transfer.js — BeeForce Configuration Portal
// Owns: screen-wft, screen-wft-upload
// Endpoint: POST /api/attendance/workflow/employee_transfer
//   Body: {externalNumber, newManager, replace (bool, default false)}
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const WFT_URL = () => `${AppState.BASE_URL}/api/attendance/workflow/employee_transfer`;

  if (!document.getElementById("screen-wft")) {
    const main = document.createElement("div");
    main.id = "screen-wft"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🔄 Workflow Transfer</span></div>
      <div class="bf-module-header"><div class="mh-icon">🔄</div><div><div class="mh-title">Workflow Transfer</div><div class="mh-sub">Bulk employee manager transfer via workflow</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="wft-action-tpl">
          <div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div>
          <div class="ac-desc">externalNumber · newManager · replace (TRUE/FALSE)</div>
        </div>
        <div class="bf-action-card" id="wft-action-upload">
          <div class="ac-icon">📤</div><div class="ac-name">Upload & Transfer</div>
          <div class="ac-desc">Posts each row; replace defaults to FALSE if blank</div>
        </div>
      </div>`;
    modal.appendChild(main);

    const upload = document.createElement("div");
    upload.id = "screen-wft-upload"; upload.style.display = "none";
    upload.innerHTML = `
      <div class="bf-breadcrumb">
        <span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span>
        <span class="bc-link" data-go="screen-wft">🔄 Workflow Transfer</span><span class="bc-sep">›</span>
        <span class="bc-cur">Upload & Transfer</span>
      </div>
      <div class="bf-info-box">
        Required: <b>externalNumber</b>, <b>newManager</b>.<br>
        <b>replace</b>: enter TRUE to replace existing manager, FALSE (or leave blank) to add.<br>
        Each row → <code>POST /api/attendance/workflow/employee_transfer</code>
      </div>
      <div id="wft-status" class="bf-status"></div>
      <label class="bf-file-label" for="wft-file"><span id="wft-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="wft-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="wft-prog"><div class="bf-pb" id="wft-bar" style="width:0%"></div></div>
      <div class="bf-log" id="wft-log"></div>
      <button class="bf-btn bf-success" id="wft-submit" disabled>🚀 Submit Transfers</button>
      <button class="bf-btn bf-outline" id="wft-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="wft-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(upload);

    Router.register("screen-wft", "screen-wft-upload");
    [main, upload].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("wft-action-tpl").onclick = () => {
    downloadExcel("workflow_transfer_template.xlsx", [{
      name: "Workflow_Transfer", tabColor: "0369A1",
      headers: ["externalNumber", "newManager", "replace (TRUE/FALSE, default FALSE)"],
      rows: [], highlightCols: [0, 1]
    }]);
  };

  document.getElementById("wft-action-upload").onclick = () => {
    Notifications.clearLog("wft-log");
    AppState.cache.wft = null; AppState.cache.wftSuccess = []; AppState.cache.wftFailed = [];
    document.getElementById("wft-submit").disabled = true;
    document.getElementById("wft-dl-success").style.display = "none";
    document.getElementById("wft-dl-failed").style.display = "none";
    Router.go("screen-wft-upload");
  };

  wireFileInput("wft-file", "wft-file-name", "wft-submit", "wft");

  document.getElementById("wft-dl-success").onclick = () => {
    downloadExcel("wft_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["externalNumber", "newManager", "replace"],
      rows: (AppState.cache.wftSuccess || []).map(r => [r.ext, r.mgr, r.replace])
    }]);
  };
  document.getElementById("wft-dl-failed").onclick = () => {
    downloadExcel("wft_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["externalNumber", "newManager", "replace", "error"],
      rows: (AppState.cache.wftFailed || []).map(r => [r.ext, r.mgr, r.replace, r.error])
    }]);
  };

  document.getElementById("wft-submit").onclick = async () => {
    const btn = document.getElementById("wft-submit");
    const rows = AppState.cache.wft || [];
    Notifications.clearLog("wft-log");
    document.getElementById("wft-dl-success").style.display = "none";
    document.getElementById("wft-dl-failed").style.display = "none";

    if (!rows.length) { Notifications.error("wft-status", "❌ No data found"); return; }

    function col(row, name) {
      const k = Object.keys(row).find(k => k.trim().toLowerCase().replace(/[^a-z0-9]/g, "") === name.toLowerCase().replace(/[^a-z0-9]/g, ""));
      return k ? String(row[k] || "").trim() : "";
    }

    const parseErrors = [], validRows = [];
    rows.forEach((row, i) => {
      const ext = col(row, "externalnumber");
      const mgr = col(row, "newmanager");
      if (!ext || !mgr) { parseErrors.push(`Row ${i + 2}: externalNumber and newManager are required`); return; }
      const replRaw = col(row, "replace") || col(row, "replacetruefalsdefaultfalse") || "";
      const repl = ["true", "1", "yes"].includes(replRaw.toLowerCase());
      validRows.push({ ext, mgr, replace: repl });
    });

    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("wft-log", `⚠️ ${e}`, "fail"); Audit.onValidationError(e); });
    if (!validRows.length) { Notifications.error("wft-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, `Processing 0/${validRows.length}...`);
    Notifications.progress.show("wft-prog");
    AppState.cache.wftSuccess = []; AppState.cache.wftFailed = [];
    let s = 0, f = 0;

    for (let i = 0; i < validRows.length; i++) {
      const { ext, mgr, replace } = validRows[i];
      try {
        const r = await ApiTracker.fetch(WFT_URL(), {
          method: "POST", headers: apiH(),
          body: JSON.stringify({ externalNumber: ext, newManager: mgr, replace })
        }, "Workflow Transfer");
        const body = await r.text();
        if (r.status === 200 || r.status === 201 || r.status === 202) {
          Notifications.log("wft-log", `✅ Transferred — ext: ${ext} → mgr: ${mgr} | replace: ${replace}`, "ok");
          AppState.cache.wftSuccess.push({ ext, mgr, replace: replace ? "TRUE" : "FALSE" });
          s++;
        } else {
          const errMsg = parseApiError(body);
          Notifications.log("wft-log", `❌ Failed — ext: ${ext} | ${errMsg}`, "fail");
          AppState.cache.wftFailed.push({ ext, mgr, replace: replace ? "TRUE" : "FALSE", error: errMsg });
          f++;
        }
      } catch (e) {
        Notifications.log("wft-log", `❌ Error — ext: ${ext} | ${e.message}`, "fail");
        AppState.cache.wftFailed.push({ ext, mgr, replace: replace ? "TRUE" : "FALSE", error: e.message });
        f++;
      }
      Notifications.progress.set("wft-bar", ((i + 1) / validRows.length) * 100);
      Notifications.loading(btn, `Processing ${i + 1}/${validRows.length}...`);
    }

    Audit.onDbOp("updated", s);
    Notifications.progress.done("wft-bar");
    Notifications.log("wft-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("wft-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("wft-status", `Done — ${s} transferred, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit Transfers");
    Notifications.progress.hide("wft-prog", 2500);
    if (AppState.cache.wftSuccess.length) document.getElementById("wft-dl-success").style.display = "block";
    if (AppState.cache.wftFailed.length) document.getElementById("wft-dl-failed").style.display = "block";
  };
}
