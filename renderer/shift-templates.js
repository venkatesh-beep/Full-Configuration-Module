/* =========================================================
 * shift-templates.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/shift-templates.js — BeeForce Configuration Portal
// Owns: screen-st, screen-st-create, screen-st-view, screen-st-delete
// GET    /api/attendance/shift_templates?projection=FULL
// POST   /api/attendance/shift_templates            (create)
// DELETE /api/attendance/shift_templates/{id}
// Exports: init(context)
// =========================================================
const ST_HEADERS = [
  "name", "description", "startTime(HH:MM)", "endTime(HH:MM)", "startDay", "endDay",
  "report", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
  "reportGroup", "optionalShiftTemplate_id", "overridePaycode_id",
  "beforeStartToleranceMinute", "afterStartToleranceMinute",
  "lateInToleranceMinute", "earlyOutToleranceMinute",
  "paycode_id", "startMinute", "endMinute", "max"
];
const ST_INPUT_COLS = [0, 2, 3, 21, 22, 24];
const ST_VIEW_HEADERS = [
  "id", "name", "description", "startTime", "endTime", "startDay", "endDay",
  "report", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
  "reportGroup", "optionalShiftTemplate_id", "overridePaycode_id",
  "beforeStartToleranceMinute", "afterStartToleranceMinute",
  "lateInToleranceMinute", "earlyOutToleranceMinute",
  "paycode_id", "startMinute", "endMinute", "max"
];
function stBuildTime(timeStr, day) {
  const d = parseInt(day) || 1;
  const dateStr = d >= 2 ? "1970-01-02" : "1970-01-01";
  const t = String(timeStr || "").trim();
  if (!t) return `${dateStr} 00:00:00`;
  const parts = t.split(":");
  return `${dateStr} ${(parts[0] || "00").padStart(2, "0")}:${(parts[1] || "00").padStart(2, "0")}:${(parts[2] || "00").padStart(2, "0")}`;
}
function stBool(val, def = false) {
  if (val === null || val === undefined || val === "") return def;
  return ["true", "1", "yes", "y"].includes(String(val).toLowerCase().trim());
}
function stFmtTime(dt) {
  if (!dt) return "";
  const parts = String(dt).split(" ");
  return parts.length > 1 ? parts[1].slice(0, 5) : String(dt).slice(0, 5);
}
function stFmtDay(dt) {
  if (!dt) return 1;
  return String(dt).split(" ")[0].endsWith("-02") ? 2 : 1;
}
function stFlattenTemplate(t) {
  const startTime = stFmtTime(t.startTime), endTime = stFmtTime(t.endTime);
  const startDay = stFmtDay(t.startTime), endDay = stFmtDay(t.endTime);
  const base = [
    t.id, t.name || "", t.description || "",
    startTime, endTime, startDay, endDay,
    t.report ? "TRUE" : "FALSE",
    t.monday ? "TRUE" : "FALSE", t.tuesday ? "TRUE" : "FALSE", t.wednesday ? "TRUE" : "FALSE",
    t.thursday ? "TRUE" : "FALSE", t.friday ? "TRUE" : "FALSE", t.saturday ? "TRUE" : "FALSE", t.sunday ? "TRUE" : "FALSE",
    t.reportGroup || "",
    t.optionalShiftTemplate?.id || "", t.overridePaycode?.id || "",
    t.beforeStartToleranceMinute || "", t.afterStartToleranceMinute || "",
    t.lateInToleranceMinute || "", t.earlyOutToleranceMinute || ""
  ];
  const rows = [];
  if (!(t.paycodes || []).length) {
    rows.push([...base, "", "", "", ""]);
  } else {
    (t.paycodes).forEach(pc => rows.push([
      ...base, pc.paycode?.id || "", pc.startMinute ?? 0,
      pc.max ? "" : (pc.endMinute ?? ""), pc.max ? "TRUE" : "FALSE"
    ]));
  }
  return rows;
}
function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, fetchPaycodesRef, modal } = ctx;
  const ST_BASE = () => `${AppState.BASE_URL}/api/attendance/shift_templates`;
  if (!document.getElementById("screen-st")) {
    const main = document.createElement("div");
    main.id = "screen-st"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📅 Shift Templates</span></div>
      <div class="bf-module-header"><div class="mh-icon">📅</div><div><div class="mh-title">Shift Templates</div><div class="mh-sub">Create · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="st-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">3 sheets — headers · existing templates · paycodes master</div></div>
        <div class="bf-action-card" id="st-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create</div><div class="ac-desc">Multiple rows per shift name = multiple paycodes</div></div>
        <div class="bf-action-card" id="st-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Fetch all templates and download as Excel</div></div>
        <div class="bf-action-card" id="st-action-update"><div class="ac-icon">✏️</div><div class="ac-name">Update Shift Templates</div><div class="ac-desc">Download existing data · edit · re-upload to PUT</div></div>
        <div class="bf-action-card" id="st-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete templates by comma-separated IDs</div></div>
      </div>`;
    modal.appendChild(main);
    const create = document.createElement("div");
    create.id = "screen-st-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-st">📅 Shift Templates</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create</span></div>
      <div class="bf-info-box">
        Each row = one paycode entry. Multiple rows with the same <b>name</b> = one shift with multiple paycodes.<br>
        <b>Red columns are mandatory.</b> Leave <b>endMinute</b> blank when <b>max = true</b>.<br>
        <b>startDay/endDay:</b> 1 = 1970-01-01, 2 = 1970-01-02 (use 2 for night shifts crossing midnight).
      </div>
      <div id="st-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="st-file"><span id="st-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="st-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="st-c-prog"><div class="bf-pb" id="st-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="st-create-log"></div>
      <button class="bf-btn bf-success" id="st-submit" disabled>🚀 Create Shift Templates</button>
      <button class="bf-btn bf-outline" id="st-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="st-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(create);
    const view = document.createElement("div");
    view.id = "screen-st-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-st">📅 Shift Templates</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>
      <div id="st-view-status" class="bf-status"></div>
      <div class="bf-progress" id="st-v-prog" style="display:none"><div class="bf-pb" id="st-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="st-fetch">⬇️ Download Shift Templates</button>`;
    modal.appendChild(view);
    const del = document.createElement("div");
    del.id = "screen-st-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-st">📅 Shift Templates</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>
      <div id="st-delete-status" class="bf-status"></div>
      <label class="bf-label">Template IDs to delete (comma-separated)</label>
      <input type="text" id="st-del-ids" placeholder="101, 102, 103" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="st-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="st-delete-log"></div>
      <button class="bf-btn bf-danger" id="st-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);
    const update = document.createElement("div");
    update.id = "screen-st-update"; update.style.display = "none";
    update.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-st">📅 Shift Templates</span><span class="bc-sep">›</span><span class="bc-cur">Update Shift Templates</span></div>
      <div class="bf-info-box">
        <b>Step 1:</b> Download — <b>Sheet 1 (Shift_Templates_Update)</b> is blank, ready to fill; <b>Sheet 2 (Existing_Shift_Templates_Ref)</b> already has every existing template, one row per paycode entry, for reference/copying.<br>
        <b>Step 2:</b> Either copy rows into Sheet 1 and edit them, or edit Sheet 2 directly — the upload reads whichever sheet actually has data (Sheet 1 first, falling back to Sheet 2).<br>
        Each row's first <b>id</b> = shift template id (PUT target). The second <b>id</b> = that specific paycode entry's own id — keep it as-is to update that entry, or leave a row's second id blank to add a brand-new paycode entry to that template.<br>
        Dates are <b>DD-MM-YYYY HH:MM</b> (e.g. <code>01-01-1970 09:35</code>).
      </div>
      <div id="st-update-status" class="bf-status"></div>
      <button class="bf-btn bf-primary" id="st-update-download" style="margin-bottom:14px;">⬇️ Download Existing Shift Templates</button>
      <label class="bf-file-label" for="st-update-file"><span id="st-update-file-name">📂 Click to select edited file (.xlsx)</span></label>
      <input type="file" id="st-update-file" class="bf-file-input" accept=".xlsx,.xls" />
      <div class="bf-progress" id="st-u-prog"><div class="bf-pb" id="st-u-bar" style="width:0%"></div></div>
      <div class="bf-log" id="st-update-log"></div>
      <button class="bf-btn bf-success" id="st-update-submit" disabled>🚀 Update Shift Templates</button>
      <button class="bf-btn bf-outline" id="st-update-cancel">✕ Cancel</button>
      <button class="bf-btn bf-outline" id="st-update-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="st-update-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(update);
    Router.register("screen-st", "screen-st-create", "screen-st-view", "screen-st-delete", "screen-st-update");
    [main, create, view, del, update].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }
  document.getElementById("st-action-tpl").onclick = async () => {
    const btn = document.getElementById("st-action-tpl"); btn.style.opacity = "0.6";
    const [stRes, pcRes] = await Promise.allSettled([
      ApiTracker.fetch(`${ST_BASE()}?projection=FULL`, { headers: apiH() }, "Shift Templates").then(r => r.ok ? r.json() : []).catch(() => []),
      fetchPaycodesRef()
    ]);
    const existing = stRes.status === "fulfilled" ? (stRes.value || []) : [];
    const paycodes = pcRes.status === "fulfilled" ? (pcRes.value || []) : [];
    const stRows = [];
    existing.forEach(t => stFlattenTemplate(t).forEach(r => stRows.push(r)));
    downloadExcel("shift_templates_template.xlsx", [
      { name: "Shift_Templates", tabColor: "1D4ED8", headers: ST_HEADERS, rows: [], highlightCols: ST_INPUT_COLS },
      { name: "Existing_Templates_Ref", tabColor: "7C3AED", headers: ST_VIEW_HEADERS, rows: stRows },
      { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "code", "description"], rows: paycodes.map(p => [p.id, p.code || "", p.description || ""]) }
    ]);
    btn.style.opacity = "1";
  };
  document.getElementById("st-action-create").onclick = () => {
    Notifications.clearLog("st-create-log");
    AppState.cache.st = null; AppState.cache.stSuccessRows = []; AppState.cache.stFailedRows = [];
    document.getElementById("st-submit").disabled = true;
    document.getElementById("st-dl-success").style.display = "none";
    document.getElementById("st-dl-failed").style.display = "none";
    Router.go("screen-st-create");
  };
  document.getElementById("st-action-view").onclick = () => Router.go("screen-st-view");
  document.getElementById("st-action-delete").onclick = () => { Notifications.clearLog("st-delete-log"); Router.go("screen-st-delete"); };
  wireFileInput("st-file", "st-file-name", "st-submit", "st");
  document.getElementById("st-dl-success").onclick = () => {
    downloadExcel("st_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["created_id", "name", "paycodes_count"], rows: (AppState.cache.stSuccessRows || []).map(r => [r.id || "", r.name, r.paycodes]) }]);
  };
  document.getElementById("st-dl-failed").onclick = () => {
    downloadExcel("st_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["name", "http_status", "error"], rows: (AppState.cache.stFailedRows || []).map(r => [r.name, r.status || "", r.error || ""]) }]);
  };
  document.getElementById("st-submit").onclick = async () => {
    const btn = document.getElementById("st-submit");
    const rows = AppState.cache.st || [];
    Notifications.clearLog("st-create-log");
    document.getElementById("st-dl-success").style.display = "none";
    document.getElementById("st-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("st-create-status", "❌ No data found"); return; }
    function col(row, name) {
      const norm = s => String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");
      const k = Object.keys(row).find(k => norm(k) === norm(name));
      return k ? String(row[k] || "").trim() : "";
    }
    if (!Object.keys(rows[0]).some(k => String(k).trim().toLowerCase() === "name")) {
      Notifications.error("st-create-status", "❌ Required column 'name' not found"); return;
    }
    const groups = {}; const parseErrors = [];
    rows.forEach((row, i) => {
      const name = col(row, "name");
      if (!name) { parseErrors.push(`Row ${i + 2}: 'name' is empty`); return; }
      if (!groups[name]) groups[name] = [];
      groups[name].push(row);
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("st-create-log", `⚠️ Skipped — ${e}`, "fail"); Audit.onValidationError(e); });
    const shiftNames = Object.keys(groups);
    if (!shiftNames.length) { Notifications.error("st-create-status", "❌ No valid rows"); return; }
    Notifications.loading(btn, `Processing 0/${shiftNames.length} shift(s)...`);
    Notifications.progress.show("st-c-prog");
    AppState.cache.stSuccessRows = []; AppState.cache.stFailedRows = [];
    let s = 0, f = 0;
    for (let i = 0; i < shiftNames.length; i++) {
      const name = shiftNames[i]; const group = groups[name]; const first = group[0];
      Notifications.loading(btn, `${i + 1}/${shiftNames.length}: ${name}...`);
      const startDay = parseInt(col(first, "startDay")) || 1;
      const endDay = parseInt(col(first, "endDay")) || 1;
      const payload = {
        name, description: col(first, "description") || name,
        startTime: stBuildTime(col(first, "startTimeHHMM") || col(first, "startTime"), startDay),
        endTime: stBuildTime(col(first, "endTimeHHMM") || col(first, "endTime"), endDay),
        startDay, endDay,
        report: stBool(col(first, "report"), true),
        monday: stBool(col(first, "monday"), true), tuesday: stBool(col(first, "tuesday"), true),
        wednesday: stBool(col(first, "wednesday"), true), thursday: stBool(col(first, "thursday"), true),
        friday: stBool(col(first, "friday"), true), saturday: stBool(col(first, "saturday"), true), sunday: stBool(col(first, "sunday"), true),
        reportGroup: col(first, "reportGroup"),
        beforeStartToleranceMinute: parseInt(col(first, "beforeStartToleranceMinute")) || 0,
        afterStartToleranceMinute: parseInt(col(first, "afterStartToleranceMinute")) || 0,
        lateInToleranceMinute: parseInt(col(first, "lateInToleranceMinute")) || 0,
        earlyOutToleranceMinute: parseInt(col(first, "earlyOutToleranceMinute")) || 0,
        paycodes: []
      };
      const optId = parseIntSafe(col(first, "optionalShiftTemplate_id") || col(first, "optionalShiftTemplateid"));
      const overId = parseIntSafe(col(first, "overridePaycode_id") || col(first, "overridePaycodeid"));
      if (optId !== null) payload.optionalShiftTemplate = { id: optId };
      if (overId !== null) payload.overridePaycode = { id: overId };
      group.forEach(row => {
        const pcId = parseIntSafe(col(row, "paycode_id") || col(row, "paycodeid"));
        if (pcId === null) return;
        const isMax = stBool(col(row, "max"), false);
        const startMin = parseInt(col(row, "startMinute"));
        const endMin = parseInt(col(row, "endMinute"));
        const entry = { paycode: { id: pcId }, startMinute: isNaN(startMin) ? 0 : startMin, max: isMax };
        if (!isMax && !isNaN(endMin)) entry.endMinute = endMin;
        payload.paycodes.push(entry);
      });
      if (!payload.paycodes.length) {
        Notifications.log("st-create-log", `⚠️ ${name}: no valid paycode rows — skipped`, "fail");
        AppState.cache.stFailedRows.push({ name, status: "SKIPPED", error: "No paycode rows found" });
        f++;
      } else {
        try {
          const r = await ApiTracker.fetch(ST_BASE(), { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Shift Templates");
          const body = await r.text();
          if (r.status === 200 || r.status === 201) {
            let createdId = ""; try { createdId = JSON.parse(body).id || ""; } catch (e) {}
            Notifications.log("st-create-log", `✅ Created: ${name} (id:${createdId}, ${payload.paycodes.length} paycode(s))`, "ok");
            AppState.cache.stSuccessRows.push({ id: createdId, name, paycodes: payload.paycodes.length });
            Audit.onDbOp("created", 1);
            s++;
          } else {
            const errMsg = parseApiError(body);
            Notifications.log("st-create-log", `❌ Failed: ${name} — ${errMsg}`, "fail");
            AppState.cache.stFailedRows.push({ name, status: r.status, error: errMsg });
            f++;
          }
        } catch (e) {
          Notifications.log("st-create-log", `❌ Error: ${name} — ${e.message}`, "fail");
          AppState.cache.stFailedRows.push({ name, status: "NETWORK_ERROR", error: e.message });
          f++;
        }
      }
      Notifications.progress.set("st-c-bar", ((i + 1) / shiftNames.length) * 100);
    }
    Notifications.log("st-create-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("st-create-log", `✅ Created: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("st-create-status", `Done — ${s} created, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Create Shift Templates");
    Notifications.progress.hide("st-c-prog");
    if (AppState.cache.stSuccessRows.length) document.getElementById("st-dl-success").style.display = "block";
    if (AppState.cache.stFailedRows.length) document.getElementById("st-dl-failed").style.display = "block";
  };
  document.getElementById("st-fetch").onclick = async () => {
    const btn = document.getElementById("st-fetch");
    Notifications.loading(btn, "Initializing...");
    Notifications.progress.show("st-v-prog");
    try {
      Notifications.info("st-view-status", "⏳ Fetching shift templates (FULL projection)..."); Notifications.progress.set("st-v-bar", 20);
      const r = await ApiTracker.fetch(`${ST_BASE()}?projection=FULL`, { headers: apiH() }, "Shift Templates");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      AppState.cache.stView = await r.json();
      Notifications.info("st-view-status", `⏳ Processing ${AppState.cache.stView.length} template(s)...`); Notifications.progress.set("st-v-bar", 60);
      const rows = [];
      (AppState.cache.stView || []).forEach(t => stFlattenTemplate(t).forEach(r => rows.push(r)));
      Notifications.info("st-view-status", "⏳ Preparing download..."); Notifications.progress.set("st-v-bar", 85);
      downloadExcel(`shift_templates_${new Date().toISOString().slice(0, 10)}.xlsx`, [{ name: "Shift_Templates", tabColor: "1D4ED8", headers: ST_VIEW_HEADERS, rows }]);
      Notifications.progress.set("st-v-bar", 100);
      Notifications.success("st-view-status", `✅ Download complete — ${AppState.cache.stView.length} template(s), ${rows.length} rows`);
    } catch (e) {
      Notifications.error("st-view-status", `❌ ${e.message}`); Notifications.progress.set("st-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Shift Templates");
      Notifications.progress.hide("st-v-prog", 2000);
    }
  };
  document.getElementById("st-do-delete").onclick = async () => {
    if (!document.getElementById("st-confirm").checked) { Notifications.error("st-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("st-del-ids").value.split(",").map(s => s.trim()).filter(s => s !== "");
    if (!ids.length) { Notifications.error("st-delete-status", "❌ No IDs entered"); return; }
    const btn = document.getElementById("st-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("st-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${ST_BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Shift Templates");
        if (r.status === 200 || r.status === 201 || r.status === 204) { Notifications.log("st-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("st-delete-log", `❌ Failed: ${id} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("st-delete-log", `❌ Error: ${id} — ${e.message}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("st-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };

  // =========================================================
  // NEW — Update Shift Templates (download existing + edit + re-upload
  // to PUT). Entirely additive — nothing above this point changed.
  // Confirmed against: PUT /api/attendance/shift_templates/{id}
  // =========================================================
  const ST_UPDATE_HEADERS = [
    "id", "name", "description", "startTime", "endTime",
    "beforeStartToleranceMinute", "afterStartToleranceMinute", "lateInToleranceMinute", "earlyOutToleranceMinute",
    "report", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "id", "Paycode ID", "startMinute", "endMinute", "max"
  ];
  // Two columns are both named "id" (shift template id, then paycode
  // entry id) — read this file positionally (header:1), not by column
  // name, since duplicate object keys would silently drop one of them.
  const SU = {
    ID: 0, NAME: 1, DESC: 2, START: 3, END: 4,
    BEFORE_TOL: 5, AFTER_TOL: 6, LATE_TOL: 7, EARLY_TOL: 8,
    REPORT: 9, MON: 10, TUE: 11, WED: 12, THU: 13, FRI: 14, SAT: 15, SUN: 16,
    ENTRY_ID: 17, PAYCODE_ID: 18, START_MIN: 19, END_MIN: 20, MAX: 21
  };

  /** "1970-01-01 09:35:00" -> "01-01-1970 09:35" */
  function stUpdFmtDateTime(apiStr) {
    if (!apiStr) return "";
    const [datePart, timePart] = String(apiStr).trim().split(" ");
    if (!datePart) return "";
    const [yyyy, mm, dd] = datePart.split("-");
    const t = (timePart || "00:00:00").split(":");
    return `${dd}-${mm}-${yyyy} ${t[0]}:${t[1]}`;
  }
  /** "01-01-1970 09:35" -> "1970-01-01 09:35:00" */
  function stUpdBuildDateTime(displayStr) {
    if (!displayStr) return "";
    const [datePart, timePart] = String(displayStr).trim().split(" ");
    if (!datePart) return "";
    const [dd, mm, yyyy] = datePart.split("-");
    const t = (timePart || "00:00").split(":");
    return `${yyyy}-${mm}-${dd} ${(t[0] || "00").padStart(2, "0")}:${(t[1] || "00").padStart(2, "0")}:00`;
  }

  function stFlattenForUpdate(t) {
    const base = [
      t.id, t.name || "", t.description || "",
      stUpdFmtDateTime(t.startTime), stUpdFmtDateTime(t.endTime),
      t.beforeStartToleranceMinute ?? "", t.afterStartToleranceMinute ?? "",
      t.lateInToleranceMinute ?? "", t.earlyOutToleranceMinute ?? "",
      t.report ? "TRUE" : "FALSE",
      t.monday ? "TRUE" : "FALSE", t.tuesday ? "TRUE" : "FALSE", t.wednesday ? "TRUE" : "FALSE",
      t.thursday ? "TRUE" : "FALSE", t.friday ? "TRUE" : "FALSE", t.saturday ? "TRUE" : "FALSE", t.sunday ? "TRUE" : "FALSE"
    ];
    const pcs = t.paycodes || [];
    if (!pcs.length) return [[...base, "", "", "", "", ""]];
    return pcs.map(pc => [
      ...base, pc.id ?? "", pc.paycode?.id ?? "", pc.startMinute ?? 0,
      pc.max ? "" : (pc.endMinute ?? ""), pc.max ? "TRUE" : "FALSE"
    ]);
  }

  document.getElementById("st-action-update").onclick = () => {
    Notifications.clearLog("st-update-log");
    AppState.cache.stUpdateRows = null; AppState.cache.stUpdateSuccess = []; AppState.cache.stUpdateFailed = [];
    document.getElementById("st-update-submit").disabled = true;
    document.getElementById("st-update-dl-success").style.display = "none";
    document.getElementById("st-update-dl-failed").style.display = "none";
    document.getElementById("st-update-file").value = "";
    document.getElementById("st-update-file-name").textContent = "📂 Click to select edited file (.xlsx)";
    Router.go("screen-st-update");
  };

  document.getElementById("st-update-cancel").onclick = () => {
    AppState.cache.stUpdateRows = null;
    document.getElementById("st-update-file").value = "";
    document.getElementById("st-update-file-name").textContent = "📂 Click to select edited file (.xlsx)";
    document.getElementById("st-update-submit").disabled = true;
    Notifications.clearLog("st-update-log");
    document.getElementById("st-update-status").className = "bf-status";
    document.getElementById("st-update-status").textContent = "";
    Router.go("screen-st");
  };

  document.getElementById("st-update-download").onclick = async () => {
    const btn = document.getElementById("st-update-download");
    Notifications.loading(btn, "Fetching...");
    try {
      Notifications.info("st-update-status", "⏳ Fetching shift templates (FULL projection)...");
      const r = await ApiTracker.fetch(`${ST_BASE()}/?projection=FULL`, { headers: apiH() }, "Shift Templates");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      const list = await r.json();
      const rows = [];
      (list || []).forEach(t => stFlattenForUpdate(t).forEach(row => rows.push(row)));
      downloadExcel(`shift_templates_update_${new Date().toISOString().slice(0, 10)}.xlsx`, [
        { name: "Shift_Templates_Update", tabColor: "16A34A", headers: ST_UPDATE_HEADERS, rows: [] },
        { name: "Existing_Shift_Templates_Ref", tabColor: "7C3AED", headers: ST_UPDATE_HEADERS, rows }
      ]);
      Notifications.success("st-update-status", `✅ Downloaded — Sheet 2 has ${list.length} template(s), ${rows.length} row(s). Fill Sheet 1 (copy/edit from Sheet 2) and re-upload below.`);
    } catch (e) {
      Notifications.error("st-update-status", `❌ ${e.message}`);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Existing Shift Templates");
    }
  };

  // Custom positional file reader — this sheet has two "id" columns,
  // which would collide under normal {colName:value} object reading.
  document.getElementById("st-update-file").addEventListener("change", (e) => {
    const file = e.target.files[0];
    const submitBtn = document.getElementById("st-update-submit");
    if (!file) { AppState.cache.stUpdateRows = null; submitBtn.disabled = true; return; }
    document.getElementById("st-update-file-name").textContent = "📄 " + file.name;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const wb = XLSX.read(new Uint8Array(ev.target.result), { type: "array" });
        const readByName = (name) => {
          const ws = wb.Sheets[name];
          if (!ws) return [];
          const aoa = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "", raw: false });
          return aoa.slice(1).filter(r => r.some(c => String(c).trim() !== ""));
        };
        let dataRows = readByName("Shift_Templates_Update");
        if (!dataRows.length) dataRows = readByName("Existing_Shift_Templates_Ref"); // fallback: edited Sheet 2 directly
        if (!dataRows.length) { // last resort: whatever sheet is first
          const ws = wb.Sheets[wb.SheetNames[0]];
          const aoa = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "", raw: false });
          dataRows = aoa.slice(1).filter(r => r.some(c => String(c).trim() !== ""));
        }
        AppState.cache.stUpdateRows = dataRows;
        submitBtn.disabled = false;
        if (Audit) Audit.onFileSelected(file.name);
      } catch (err) {
        Notifications.alert("❌ Failed to read file: " + err.message);
        AppState.cache.stUpdateRows = null; submitBtn.disabled = true;
      }
    };
    reader.onerror = () => { Notifications.alert("❌ Failed to read file"); submitBtn.disabled = true; };
    reader.readAsArrayBuffer(file);
  });

  document.getElementById("st-update-dl-success").onclick = () => {
    downloadExcel("st_update_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["id", "name", "paycodes_count"], rows: (AppState.cache.stUpdateSuccess || []).map(r => [r.id || "", r.name, r.paycodes]) }]);
  };
  document.getElementById("st-update-dl-failed").onclick = () => {
    downloadExcel("st_update_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["id", "name", "http_status", "error"], rows: (AppState.cache.stUpdateFailed || []).map(r => [r.id || "", r.name, r.status || "", r.error || ""]) }]);
  };

  function stBuildUpdatePayload(group) {
    const first = group[0];
    const payload = {
      id: parseInt(first[SU.ID]),
      name: String(first[SU.NAME] || "").trim(),
      description: String(first[SU.DESC] || "").trim(),
      startTime: stUpdBuildDateTime(first[SU.START]),
      endTime: stUpdBuildDateTime(first[SU.END]),
      beforeStartToleranceMinute: parseInt(first[SU.BEFORE_TOL]) || 0,
      afterStartToleranceMinute: parseInt(first[SU.AFTER_TOL]) || 0,
      lateInToleranceMinute: parseInt(first[SU.LATE_TOL]) || 0,
      earlyOutToleranceMinute: parseInt(first[SU.EARLY_TOL]) || 0,
      report: stBool(first[SU.REPORT], false),
      monday: stBool(first[SU.MON], false), tuesday: stBool(first[SU.TUE], false), wednesday: stBool(first[SU.WED], false),
      thursday: stBool(first[SU.THU], false), friday: stBool(first[SU.FRI], false), saturday: stBool(first[SU.SAT], false), sunday: stBool(first[SU.SUN], false),
      paycodes: []
    };
    group.forEach(row => {
      const paycodeRefId = parseIntSafe(row[SU.PAYCODE_ID]);
      if (paycodeRefId === null) return;
      const entryId = parseIntSafe(row[SU.ENTRY_ID]);
      const isMax = stBool(row[SU.MAX], false);
      const startMin = parseInt(row[SU.START_MIN]);
      const endMin = parseInt(row[SU.END_MIN]);
      const entry = { paycode: { id: paycodeRefId }, startMinute: isNaN(startMin) ? 0 : startMin, max: isMax };
      if (entryId !== null) entry.id = entryId; // preserve existing entry identity; omit to add a new entry
      if (!isMax && !isNaN(endMin)) entry.endMinute = endMin;
      payload.paycodes.push(entry);
    });
    return payload;
  }

  document.getElementById("st-update-submit").onclick = async () => {
    const btn = document.getElementById("st-update-submit");
    const rows = AppState.cache.stUpdateRows || [];
    Notifications.clearLog("st-update-log");
    document.getElementById("st-update-dl-success").style.display = "none";
    document.getElementById("st-update-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("st-update-status", "❌ No data found"); return; }

    const groups = {};
    const parseErrors = [];
    rows.forEach((row, i) => {
      const id = parseIntSafe(row[SU.ID]);
      if (id === null) { parseErrors.push(`Row ${i + 2}: shift template id is required`); return; }
      if (!groups[id]) groups[id] = [];
      groups[id].push(row);
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("st-update-log", `⚠️ ${e}`, "fail"); Audit.onValidationError(e); });

    const ids = Object.keys(groups);
    const total = ids.length;
    if (!total) { Notifications.error("st-update-status", "❌ No valid rows found"); return; }

    Notifications.loading(btn, `Updating 0/${total}...`);
    Notifications.progress.show("st-u-prog");
    AppState.cache.stUpdateSuccess = []; AppState.cache.stUpdateFailed = [];
    let s = 0, f = 0;

    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const group = groups[id];
      const payload = stBuildUpdatePayload(group);
      Notifications.loading(btn, `${i + 1}/${total}: ${payload.name}...`);
      try {
        const r = await ApiTracker.fetch(`${ST_BASE()}/${id}`, { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Shift Templates");
        const body = await r.text();
        if (r.ok) {
          Notifications.log("st-update-log", `✅ Updated: ${payload.name} (id:${id}, ${payload.paycodes.length} paycode(s))`, "ok");
          AppState.cache.stUpdateSuccess.push({ id, name: payload.name, paycodes: payload.paycodes.length });
          Audit.onDbOp("updated", 1); s++;
        } else {
          const errMsg = parseApiError(body);
          Notifications.log("st-update-log", `❌ Failed: ${payload.name} (id:${id}) — ${errMsg}`, "fail");
          AppState.cache.stUpdateFailed.push({ id, name: payload.name, status: r.status, error: errMsg }); f++;
        }
      } catch (e) {
        Notifications.log("st-update-log", `❌ Error: ${payload.name} (id:${id}) — ${e.message}`, "fail");
        AppState.cache.stUpdateFailed.push({ id, name: payload.name, status: "NETWORK_ERROR", error: e.message }); f++;
      }
      Notifications.progress.set("st-u-bar", ((i + 1) / total) * 100);
    }

    Notifications.log("st-update-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("st-update-log", `✅ Updated: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("st-update-status", `Done — ${s} updated, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Update Shift Templates");
    Notifications.progress.hide("st-u-prog");
    if (AppState.cache.stUpdateSuccess.length) document.getElementById("st-update-dl-success").style.display = "block";
    if (AppState.cache.stUpdateFailed.length) document.getElementById("st-update-dl-failed").style.display = "block";
  };

  console.log("✅ Shift Templates module loaded — Create · View · Delete · Update");
}