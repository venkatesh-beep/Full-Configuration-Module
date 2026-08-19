/* =========================================================
 * regularization-policy-sets.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-regpolset, screen-regpolset-create
 * POST /api/compliance/template/filed/save  (SAME URL for create AND
 *      update — presence of "id" in the body is what makes it an
 *      update, matching the pattern confirmed elsewhere in this app)
 *
 * NOTE: only a create/update curl was provided for this resource — no
 * GET (list/view) or DELETE endpoint. "View Existing" and "Delete" are
 * intentionally left out of this module until those are shared; the
 * hub screen says so explicitly rather than guessing at endpoints.
 *
 * NOTE ALSO: the endpoints given (/api/compliance/template/filed/save,
 * payload shape templateId/filedName/filedType/monthly/yearly/...)
 * describe a Compliance Template Field, not what "Regularization
 * Policy Set" would normally suggest. Built exactly as given — if this
 * was meant for a different module/file, let me know and I'll move it.
 * ========================================================= */

const REGPOLSET_HEADERS = [
  "ID (blank=create)", "Template ID", "Filed Name", "Sequence",
  "Mandatory", "Active", "Filed Type", "Monthly", "Yearly", "Org ID", "Template Name"
];
const REGPOLSET_INPUT_COLS = [1, 2, 3];

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const REGPOLSET_SAVE_URL = () => `${AppState.BASE_URL}/api/compliance/template/filed/save`;

  const col = (row, name) => {
    const n = name.toLowerCase().replace(/[^a-z0-9]/g, "");
    const k = Object.keys(row).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, "") === n);
    return k ? String(row[k] || "").trim() : "";
  };
  const toBool = v => ["true", "1", "yes"].includes(String(v || "").toLowerCase().trim());

  if (!document.getElementById("screen-regpolset")) {
    const main = document.createElement("div");
    main.id = "screen-regpolset"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📐 Regularization Policy Set</span></div>
      <div class="bf-module-header"><div class="mh-icon">📐</div><div><div class="mh-title">Regularization Policy Set</div><div class="mh-sub">Create · Update (compliance template fields)</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="regpolset-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet — id blank = create, filled = update</div></div>
        <div class="bf-action-card" id="regpolset-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Same URL for both — id in the row decides which</div></div>
      </div>
      <div style="background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:14px 16px;margin-top:14px;">
        <div style="font-weight:700;color:#92400E;margin-bottom:4px;">⚠️ View Existing / Delete not available yet</div>
        <div style="font-size:12px;color:#78350F;">Only a create/update endpoint was provided for this resource. Share a working GET (list) and DELETE curl and those actions will be added the same way as every other module.</div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-regpolset-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-regpolset">📐 Regularization Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>
      <div class="bf-info-box">
        <b>ID</b> blank = create, filled = update — both use the same POST endpoint.<br>
        <b>Mandatory</b>, <b>Active</b>, <b>Monthly</b>, <b>Yearly</b>: enter <b>TRUE</b> or <b>FALSE</b>.<br>
        <b>Org ID</b> defaults to <code>0</code> if left blank (matches your confirmed examples).
      </div>
      <div id="regpolset-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="regpolset-file"><span id="regpolset-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="regpolset-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="regpolset-c-prog"><div class="bf-pb" id="regpolset-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="regpolset-create-log"></div>
      <button class="bf-btn bf-success" id="regpolset-submit" disabled>🚀 Submit</button>
      <button class="bf-btn bf-outline" id="regpolset-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="regpolset-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(create);

    Router.register("screen-regpolset", "screen-regpolset-create");
    [main, create].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("regpolset-action-tpl").onclick = () => {
    downloadExcel("regularization_policy_set_template.xlsx", [
      { name: "Upload_Template", tabColor: "1D4ED8", headers: REGPOLSET_HEADERS, rows: [], highlightCols: REGPOLSET_INPUT_COLS }
    ]);
  };

  document.getElementById("regpolset-action-create").onclick = () => {
    Notifications.clearLog("regpolset-create-log");
    AppState.cache.regpolset = null; AppState.cache.regpolsetSuccess = []; AppState.cache.regpolsetFailed = [];
    document.getElementById("regpolset-submit").disabled = true;
    document.getElementById("regpolset-dl-success").style.display = "none";
    document.getElementById("regpolset-dl-failed").style.display = "none";
    Router.go("screen-regpolset-create");
  };

  wireFileInput("regpolset-file", "regpolset-file-name", "regpolset-submit", "regpolset");

  document.getElementById("regpolset-dl-success").onclick = () => {
    downloadExcel("regpolset_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["id", "filed_name", "action"], rows: (AppState.cache.regpolsetSuccess || []).map(r => [r.id || "", r.name, r.action]) }]);
  };
  document.getElementById("regpolset-dl-failed").onclick = () => {
    downloadExcel("regpolset_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["filed_name", "http_status", "error"], rows: (AppState.cache.regpolsetFailed || []).map(r => [r.name, r.status || "", r.error || ""]) }]);
  };

  document.getElementById("regpolset-submit").onclick = async () => {
    const btn = document.getElementById("regpolset-submit");
    const rows = AppState.cache.regpolset || [];
    Notifications.clearLog("regpolset-create-log");
    document.getElementById("regpolset-dl-success").style.display = "none";
    document.getElementById("regpolset-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("regpolset-create-status", "❌ No data found"); return; }

    const valid = [], parseErrors = [];
    rows.forEach((row, i) => {
      const filedName = col(row, "Filed Name");
      const templateId = parseIntSafe(col(row, "Template ID"));
      if (!filedName) { parseErrors.push(`Row ${i + 2}: Filed Name is required`); return; }
      if (templateId === null) { parseErrors.push(`Row ${i + 2}: Template ID is required`); return; }
      valid.push(row);
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("regpolset-create-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });
    if (!valid.length) { Notifications.error("regpolset-create-status", "❌ No valid rows found"); return; }

    const total = valid.length;
    Notifications.loading(btn, `Submitting 0/${total}...`);
    Notifications.progress.show("regpolset-c-prog");
    AppState.cache.regpolsetSuccess = []; AppState.cache.regpolsetFailed = [];
    let s = 0, f = 0;

    for (let i = 0; i < valid.length; i++) {
      const row = valid[i];
      const rowId = parseIntSafe(col(row, "ID (blank=create)") || col(row, "ID"));
      const filedName = col(row, "Filed Name");
      const payload = {
        templateId: parseIntSafe(col(row, "Template ID")),
        filedName: filedName,
        sequence: parseIntSafe(col(row, "Sequence")) || 0,
        mandatory: toBool(col(row, "Mandatory")),
        active: toBool(col(row, "Active") || "true"),
        filedType: col(row, "Filed Type") || "Text",
        monthly: toBool(col(row, "Monthly")),
        yearly: toBool(col(row, "Yearly")),
        orgId: parseIntSafe(col(row, "Org ID")) || 0,
        templateName: col(row, "Template Name") || ""
      };
      if (rowId !== null) payload.id = rowId;
      const isUpdate = rowId !== null;

      try {
        const r = await ApiTracker.fetch(REGPOLSET_SAVE_URL(), { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Regularization Policy Set");
        const body = await r.text();
        if (r.ok) {
          let rid = rowId || "";
          if (!isUpdate) { try { rid = JSON.parse(body).id || ""; } catch (e) {} }
          Notifications.log("regpolset-create-log", `✅ ${isUpdate ? "Updated" : "Created"}: "${filedName}"`, "ok");
          AppState.cache.regpolsetSuccess.push({ id: rid, name: filedName, action: isUpdate ? "Updated" : "Created" });
          Audit.onDbOp(isUpdate ? "updated" : "created", 1); s++;
        } else {
          const err = parseApiError(body);
          Notifications.log("regpolset-create-log", `❌ Failed: "${filedName}" — ${err}`, "fail");
          AppState.cache.regpolsetFailed.push({ name: filedName, status: r.status, error: err }); f++;
        }
      } catch (e) {
        Notifications.log("regpolset-create-log", `❌ Error: "${filedName}" — ${e.message}`, "fail");
        AppState.cache.regpolsetFailed.push({ name: filedName, status: "NET", error: e.message }); f++;
      }
      Notifications.progress.set("regpolset-c-bar", ((i + 1) / total) * 100);
      Notifications.loading(btn, `Submitting ${i + 1}/${total}...`);
    }

    Notifications.log("regpolset-create-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("regpolset-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("regpolset-create-status", `Done — ${s} processed, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit");
    Notifications.progress.hide("regpolset-c-prog");
    if (AppState.cache.regpolsetSuccess.length) document.getElementById("regpolset-dl-success").style.display = "block";
    if (AppState.cache.regpolsetFailed.length) document.getElementById("regpolset-dl-failed").style.display = "block";
  };

  console.log("✅ Regularization Policy Set module loaded — create/update only (no GET/DELETE endpoint provided yet)");
}