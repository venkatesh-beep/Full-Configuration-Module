/* =========================================================
 * accrual.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/accrual.js — BeeForce Configuration Portal
// Owns: screen-accrual, screen-accrual-create, screen-accrual-view, screen-accrual-delete
// Endpoints:
//   POST /api/attendance/accruals/          create {"name","description"}
//   PUT  /api/attendance/accruals/{id}      update {"id","name","description"}
//   GET  /api/attendance/accruals/          view
//   DELETE /api/attendance/accruals/{id}    delete
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const ACCRUAL_BASE = () => `${AppState.BASE_URL}/api/attendance/accruals`;

  if (!document.getElementById("screen-accrual")) {
    const main = document.createElement("div");
    main.id = "screen-accrual"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🏦 Accrual</span></div>
      <div class="bf-module-header"><div class="mh-icon">🏦</div><div><div class="mh-title">Accrual</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="accrual-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">id (blank=create) · name · description</div></div>
        <div class="bf-action-card" id="accrual-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create / Update</div><div class="ac-desc">Fill id to update (PUT), leave blank to create (POST)</div></div>
        <div class="bf-action-card" id="accrual-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Download all accruals as Excel</div></div>
        <div class="bf-action-card" id="accrual-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete by comma-separated IDs</div></div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-accrual-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrual">🏦 Accrual</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create / Update</span></div>
      <div class="bf-info-box">
        Columns: <b>id</b> (leave blank to create, fill to update), <b>name</b> (required), <b>description</b> (optional).<br>
        Blank id → <code>POST /api/attendance/accruals/</code><br>
        Filled id → <code>PUT /api/attendance/accruals/{id}</code>
      </div>
      <div id="accrual-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="accrual-file"><span id="accrual-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="accrual-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="accrual-c-prog"><div class="bf-pb" id="accrual-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="accrual-create-log"></div>
      <button class="bf-btn bf-success" id="accrual-submit" disabled>🚀 Create / Update Accruals</button>
      <button class="bf-btn bf-outline" id="accrual-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="accrual-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-accrual-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrual">🏦 Accrual</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>
      <div id="accrual-view-status" class="bf-status"></div>
      <div class="bf-progress" id="accrual-v-prog" style="display:none"><div class="bf-pb" id="accrual-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="accrual-fetch">⬇️ Download Accruals</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-accrual-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrual">🏦 Accrual</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>
      <div id="accrual-delete-status" class="bf-status"></div>
      <label class="bf-label">Accrual IDs to delete (comma-separated)</label>
      <input type="text" id="accrual-del-ids" placeholder="101, 102, 103" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="accrual-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="accrual-delete-log"></div>
      <button class="bf-btn bf-danger" id="accrual-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-accrual", "screen-accrual-create", "screen-accrual-view", "screen-accrual-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("accrual-action-tpl").onclick = () => {
    downloadExcel("accrual_template.xlsx", [{ name: "Accruals", tabColor: "0369A1", headers: ["id", "name", "description"], rows: [], highlightCols: [1] }]);
  };

  document.getElementById("accrual-action-create").onclick = () => {
    Notifications.clearLog("accrual-create-log");
    AppState.cache.accrual = null; AppState.cache.accrualSuccess = []; AppState.cache.accrualFailed = [];
    document.getElementById("accrual-submit").disabled = true;
    document.getElementById("accrual-dl-success").style.display = "none";
    document.getElementById("accrual-dl-failed").style.display = "none";
    Router.go("screen-accrual-create");
  };
  document.getElementById("accrual-action-view").onclick = () => Router.go("screen-accrual-view");
  document.getElementById("accrual-action-delete").onclick = () => { Notifications.clearLog("accrual-delete-log"); Router.go("screen-accrual-delete"); };

  wireFileInput("accrual-file", "accrual-file-name", "accrual-submit", "accrual");

  document.getElementById("accrual-dl-success").onclick = () => {
    downloadExcel("accrual_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["id", "name", "description", "action"],
      rows: (AppState.cache.accrualSuccess || []).map(r => [r.id || "", r.name, r.description || "", r.action])
    }]);
  };
  document.getElementById("accrual-dl-failed").onclick = () => {
    downloadExcel("accrual_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["id", "name", "description", "error"],
      rows: (AppState.cache.accrualFailed || []).map(r => [r.id || "", r.name, r.description || "", r.error || ""])
    }]);
  };

  document.getElementById("accrual-submit").onclick = async () => {
    const btn = document.getElementById("accrual-submit");
    const rows = AppState.cache.accrual || [];
    Notifications.clearLog("accrual-create-log");
    document.getElementById("accrual-dl-success").style.display = "none";
    document.getElementById("accrual-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("accrual-create-status", "❌ No data found"); return; }

    function col(row, name) {
      const norm = s => String(s).toLowerCase().replace(/[^a-z0-9]/g, "");
      const k = Object.keys(row).find(k => norm(k) === norm(name));
      return k ? String(row[k] || "").trim() : "";
    }

    const parseErrors = [], validRows = [];
    rows.forEach((row, i) => {
      const rawId = col(row, "id"); const name = col(row, "name"); const desc = col(row, "description");
      if (!name) { parseErrors.push(`Row ${i + 2}: 'name' is required`); return; }
      validRows.push({ rawId, name, description: desc });
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("accrual-create-log", `⚠️ ${e}`, "fail"); Audit.onValidationError(e); });
    if (!validRows.length) { Notifications.error("accrual-create-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, `Processing 0/${validRows.length}...`);
    Notifications.progress.show("accrual-c-prog");
    AppState.cache.accrualSuccess = []; AppState.cache.accrualFailed = [];
    let s = 0, f = 0;

    for (let i = 0; i < validRows.length; i++) {
      const { rawId, name, description } = validRows[i];
      const existingId = parseIntSafe(rawId);
      const isUpdate = existingId !== null;
      const payload = { name, description };
      if (isUpdate) payload.id = existingId;
      const url = isUpdate ? `${ACCRUAL_BASE()}/${existingId}` : `${ACCRUAL_BASE()}/`;
      const method = isUpdate ? "PUT" : "POST";

      try {
        const r = await ApiTracker.fetch(url, { method, headers: apiH(), body: JSON.stringify(payload) }, "Accrual");
        const body = await r.text();
        if (r.status === 200 || r.status === 201) {
          let createdId = existingId || "";
          try { const j = JSON.parse(body); createdId = j.id || createdId; } catch (e) {}
          const action = isUpdate ? "Updated" : "Created";
          Notifications.log("accrual-create-log", `✅ ${action}: "${name}" (id: ${createdId})`, "ok");
          AppState.cache.accrualSuccess.push({ id: createdId, name, description, action });
          Audit.onDbOp(isUpdate ? "updated" : "created", 1);
          s++;
        } else {
          const errMsg = parseApiError(body);
          Notifications.log("accrual-create-log", `❌ Failed: "${name}" — ${errMsg}`, "fail");
          AppState.cache.accrualFailed.push({ id: rawId || "", name, description, error: errMsg });
          f++;
        }
      } catch (e) {
        Notifications.log("accrual-create-log", `❌ Error: "${name}" — ${e.message}`, "fail");
        AppState.cache.accrualFailed.push({ id: rawId || "", name, description, error: e.message });
        f++;
      }
      Notifications.progress.set("accrual-c-bar", ((i + 1) / validRows.length) * 100);
      Notifications.loading(btn, `Processing ${i + 1}/${validRows.length}...`);
      if (i === validRows.length - 1) Notifications.progress.done("accrual-c-bar");
    }

    Notifications.log("accrual-create-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("accrual-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("accrual-create-status", `Done — ${s} processed, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Create / Update Accruals");
    Notifications.progress.hide("accrual-c-prog", 2500);
    if (AppState.cache.accrualSuccess.length) document.getElementById("accrual-dl-success").style.display = "block";
    if (AppState.cache.accrualFailed.length) document.getElementById("accrual-dl-failed").style.display = "block";
  };

  document.getElementById("accrual-fetch").onclick = async () => {
    const btn = document.getElementById("accrual-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("accrual-v-prog");
    try {
      Notifications.info("accrual-view-status", "⏳ Fetching accruals..."); Notifications.progress.set("accrual-v-bar", 25);
      const r = await ApiTracker.fetch(`${ACCRUAL_BASE()}/`, { headers: apiH() }, "Accrual");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      const raw = await r.json();
      const list = Array.isArray(raw) ? raw : (raw.content || raw.data || []);
      if (!list.length) { Notifications.info("accrual-view-status", "ℹ️ No accruals found."); return; }

      Notifications.info("accrual-view-status", `⏳ Processing ${list.length} record(s)...`); Notifications.progress.set("accrual-v-bar", 70);
      const rows = list.map(a => [a.id || "", a.name || "", a.description || ""]);

      Notifications.info("accrual-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("accrual-v-bar", 90);
      downloadExcel(`accruals_${new Date().toISOString().slice(0, 10)}.xlsx`, [{ name: "Accruals", tabColor: "0369A1", headers: ["id", "name", "description"], rows }]);
      Notifications.progress.done("accrual-v-bar");
      Notifications.success("accrual-view-status", `✅ Download complete — ${list.length} accrual(s)`);
    } catch (e) {
      Notifications.error("accrual-view-status", `❌ ${e.message}`); Notifications.progress.set("accrual-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Accruals");
      Notifications.progress.hide("accrual-v-prog", 2500);
    }
  };

  document.getElementById("accrual-do-delete").onclick = async () => {
    if (!document.getElementById("accrual-confirm").checked) { Notifications.error("accrual-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("accrual-del-ids").value.split(",").map(s => s.trim()).filter(s => s !== "");
    if (!ids.length) { Notifications.error("accrual-delete-status", "❌ No IDs entered"); return; }
    const btn = document.getElementById("accrual-do-delete");
    Notifications.loading(btn, "Deleting...");
    Notifications.clearLog("accrual-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${ACCRUAL_BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Accrual");
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("accrual-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("accrual-delete-log", `❌ Failed: ${id} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("accrual-delete-log", `❌ Error: ${id} — ${e.message}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("accrual-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };
}
