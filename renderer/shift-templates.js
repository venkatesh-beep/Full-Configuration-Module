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

    Router.register("screen-st", "screen-st-create", "screen-st-view", "screen-st-delete");
    [main, create, view, del].forEach(el => {
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

  console.log("✅ Shift Templates module loaded — Create · View · Delete");
}
