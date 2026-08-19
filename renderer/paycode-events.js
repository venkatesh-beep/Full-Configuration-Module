/* =========================================================
 * paycode-events.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/paycode-events.js — BeeForce Configuration Portal
// Owns: screen-pe, screen-pe-create, screen-pe-view, screen-pe-delete
// GET    /api/attendance/paycode_events
// POST   /api/attendance/paycode_events            (create)
// PUT    /api/attendance/paycode_events/{id}        (update)
// DELETE /api/attendance/paycode_events/{id}
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, Notifications, Router, Audit, ApiTracker, fetchPaycodesRef, modal } = ctx;
  const BASE = () => `${AppState.BASE_URL}/api/attendance/paycode_events`;

  if (!document.getElementById("screen-pe")) {
    const main = document.createElement("div");
    main.id = "screen-pe"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📊 Paycode Events</span></div>
      <div class="bf-module-header"><div class="mh-icon">📊</div><div><div class="mh-title">Paycode Events</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="pe-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div></div>
        <div class="bf-action-card" id="pe-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div></div>
        <div class="bf-action-card" id="pe-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div></div>
        <div class="bf-action-card" id="pe-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div></div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-pe-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pe">📊 Paycode Events</span><span class="bc-sep">›</span><span class="bc-cur">Create/Update</span></div>
      <div class="bf-info-box">Leave <b>id</b> blank to create, fill to update.</div>
      <div id="pe-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="pe-file"><span id="pe-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="pe-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="pe-c-prog"><div class="bf-pb" id="pe-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="pe-create-log"></div>
      <button class="bf-btn bf-success" id="pe-submit" disabled>🚀 Submit Paycode Events</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-pe-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pe">📊 Paycode Events</span><span class="bc-sep">›</span><span class="bc-cur">View</span></div>
      <div id="pe-view-status" class="bf-status"></div>
      <div class="bf-progress" id="pe-v-prog" style="display:none"><div class="bf-pb" id="pe-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="pe-fetch">⬇️ Download Paycode Events</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-pe-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pe">📊 Paycode Events</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>
      <div id="pe-delete-status" class="bf-status"></div>
      <label class="bf-label">IDs to delete (comma-separated)</label>
      <input type="text" id="pe-del-ids" placeholder="101, 102, 103" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="pe-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="pe-delete-log"></div>
      <button class="bf-btn bf-danger" id="pe-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-pe", "screen-pe-create", "screen-pe-view", "screen-pe-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("pe-action-tpl").onclick = async () => {
    const btn = document.getElementById("pe-action-tpl"); btn.style.opacity = "0.6";
    const pcs = await fetchPaycodesRef();
    downloadExcel("paycode_events_template.xlsx", [
      { name: "Paycode_Events", tabColor: "1D4ED8",
        headers: ["id", "Paycode Event Name", "Description", "paycode_id", "holiday_name", "holiday_date(YYYY-MM-DD)", "repeatWeek", "repeatWeekday"],
        rows: [], highlightCols: [1, 3, 4, 5] },
      { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "code", "description"], rows: pcs.map(p => [p.id, p.code || "", p.description || ""]) }
    ]);
    btn.style.opacity = "1";
  };
  document.getElementById("pe-action-create").onclick = () => {
    Notifications.clearLog("pe-create-log"); AppState.cache.pe = null;
    document.getElementById("pe-submit").disabled = true;
    document.getElementById("pe-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    Router.go("screen-pe-create");
  };
  document.getElementById("pe-action-view").onclick = () => Router.go("screen-pe-view");
  document.getElementById("pe-action-delete").onclick = () => { Notifications.clearLog("pe-delete-log"); Router.go("screen-pe-delete"); };
  wireFileInput("pe-file", "pe-file-name", "pe-submit", "pe");

  document.getElementById("pe-submit").onclick = async () => {
    const btn = document.getElementById("pe-submit");
    const rows = AppState.cache.pe || [];
    Notifications.clearLog("pe-create-log");
    if (!rows.length) { Notifications.error("pe-create-status", "❌ No data found"); return; }

    const store = {};
    for (const row of rows) {
      const rawId = String(row["id"] || "").trim(), name = String(row["Paycode Event Name"] || "").trim();
      const desc = String(row["Description"] || "").trim() || name, pcId = String(row["paycode_id"] || "").trim();
      const hName = String(row["holiday_name"] || "").trim(), hDate = String(row["holiday_date(YYYY-MM-DD)"] || "").trim();
      const rW = String(row["repeatWeek"] || "*").trim() || "*", rWd = String(row["repeatWeekday"] || "*").trim() || "*";
      if (!name || !pcId || !hName || !hDate) { Notifications.log("pe-create-log", `⚠️ Skipped: ${name || "(no name)"}`, "fail"); continue; }
      const parts = hDate.split("-").map(Number);
      if (parts.length !== 3 || parts.some(isNaN)) { Notifications.log("pe-create-log", `⚠️ Bad date: ${hDate}`, "fail"); continue; }
      const [yr, mo, dy] = parts; const key = rawId || name;
      if (!store[key]) { const base = { name, description: desc, paycode: { id: parseInt(pcId) }, schedules: [] }; if (rawId && !isNaN(rawId)) base.id = parseInt(rawId); store[key] = base; }
      store[key].schedules.push({ name: hName, startDate: "2026-01-01", repeatDay: dy, repeatMonth: mo, repeatYear: yr, repeatWeek: rW, repeatWeekday: rWd });
    }
    const payloads = Object.values(store);
    if (!payloads.length) { Notifications.error("pe-create-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("pe-c-prog");
    let s = 0, f = 0;
    for (let i = 0; i < payloads.length; i++) {
      const p = payloads[i], isU = typeof p.id === "number";
      try {
        const r = await ApiTracker.fetch(isU ? `${BASE()}/${p.id}` : `${BASE()}`, { method: isU ? "PUT" : "POST", headers: apiH(), body: JSON.stringify(p) }, "Paycode Events");
        if (r.ok) { Notifications.log("pe-create-log", `✅ ${isU ? "Updated" : "Created"}: ${p.name}`, "ok"); s++; Audit.onDbOp(isU ? "updated" : "created", 1); }
        else { Notifications.log("pe-create-log", `❌ Failed: ${p.name} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("pe-create-log", `❌ Error: ${p.name} — ${e.message}`, "fail"); f++; }
      Notifications.progress.set("pe-c-bar", ((i + 1) / payloads.length) * 100);
    }
    Notifications.log("pe-create-log", `━━━━━━━━━━━━━━━━━━`, "info");
    Notifications.log("pe-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("pe-create-status", `Done — ${s} success, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit Paycode Events");
    Notifications.progress.hide("pe-c-prog");
  };

  document.getElementById("pe-do-delete").onclick = async () => {
    if (!document.getElementById("pe-confirm").checked) { Notifications.error("pe-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("pe-del-ids").value.split(",").map(s => s.trim()).filter(s => !isNaN(s) && s !== "");
    if (!ids.length) { Notifications.error("pe-delete-status", "❌ No valid IDs"); return; }
    const btn = document.getElementById("pe-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("pe-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Paycode Events");
        if (r.status === 200 || r.status === 204) { Notifications.log("pe-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("pe-delete-log", `❌ Failed: ${id}`, "fail"); f++; }
      } catch (e) { Notifications.log("pe-delete-log", `❌ Error: ${id}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("pe-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };

  document.getElementById("pe-fetch").onclick = async () => {
    const btn = document.getElementById("pe-fetch");
    Notifications.loading(btn, "Connecting to server...");
    Notifications.progress.show("pe-v-prog");
    try {
      Notifications.info("pe-view-status", "⏳ Fetching records..."); Notifications.progress.set("pe-v-bar", 25);
      const r = await ApiTracker.fetch(`${BASE()}`, { headers: apiH() }, "Paycode Events");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      AppState.cache.peView = await r.json();
      Notifications.info("pe-view-status", `⏳ Processing ${AppState.cache.peView.length} record(s)...`); Notifications.progress.set("pe-v-bar", 60);
      const rows = [];
      (AppState.cache.peView || []).forEach(e => (e.schedules || []).forEach(s => rows.push([
        e.id, e.name, e.description, e.paycode?.id, s.name,
        `${s.repeatYear}-${String(s.repeatMonth).padStart(2, "0")}-${String(s.repeatDay).padStart(2, "0")}`,
        s.repeatWeek, s.repeatWeekday
      ])));
      if (!rows.length) { Notifications.info("pe-view-status", "ℹ️ No records available to download."); return; }
      Notifications.info("pe-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("pe-v-bar", 85);
      downloadExcel("paycode_events_existing.xlsx", [{
        name: "Paycode_Events", tabColor: "1D4ED8",
        headers: ["id", "Paycode Event Name", "Description", "paycode_id", "holiday_name", "holiday_date(YYYY-MM-DD)", "repeatWeek", "repeatWeekday"],
        rows
      }]);
      Notifications.progress.set("pe-v-bar", 100);
      Notifications.success("pe-view-status", `✅ Download complete — ${AppState.cache.peView.length} record(s)`);
    } catch (e) {
      Notifications.error("pe-view-status", `❌ ${e.message}`); Notifications.progress.set("pe-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Paycode Events");
      Notifications.progress.hide("pe-v-prog", 2000);
    }
  };
}
