/* =========================================================
 * paycode-event-sets.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/paycode-event-sets.js — BeeForce Configuration Portal
// Owns: screen-pes, screen-pes-create, screen-pes-view, screen-pes-delete
// GET  /api/attendance/paycode_event_sets/?projection=FULL
// POST /api/attendance/paycode_event_sets/          (create)
// PUT  /api/attendance/paycode_event_sets/{id}      (update)
// DELETE /api/attendance/paycode_event_sets/{id}
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, fetchPaycodeEventsRef, modal } = ctx;
  const BASE = () => `${AppState.BASE_URL}/api/attendance/paycode_event_sets`;

  if (!document.getElementById("screen-pes")) {
    const main = document.createElement("div");
    main.id = "screen-pes"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🗂️ Event Sets</span></div>
      <div class="bf-module-header"><div class="mh-icon">🗂️</div><div><div class="mh-title">Paycode Event Sets</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="pes-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div></div>
        <div class="bf-action-card" id="pes-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div></div>
        <div class="bf-action-card" id="pes-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div></div>
        <div class="bf-action-card" id="pes-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div></div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-pes-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pes">🗂️ Event Sets</span><span class="bc-sep">›</span><span class="bc-cur">Create/Update</span></div>
      <div class="bf-info-box">Leave <b>set_id</b> blank to create. Fill to update. Multiple rows = multiple entries.</div>
      <div id="pes-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="pes-file"><span id="pes-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="pes-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="pes-c-prog"><div class="bf-pb" id="pes-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="pes-create-log"></div>
      <button class="bf-btn bf-success" id="pes-submit" disabled>🚀 Submit Paycode Event Sets</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-pes-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pes">🗂️ Event Sets</span><span class="bc-sep">›</span><span class="bc-cur">View</span></div>
      <div id="pes-view-status" class="bf-status"></div>
      <div class="bf-progress" id="pes-v-prog" style="display:none"><div class="bf-pb" id="pes-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="pes-fetch">⬇️ Download Event Sets</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-pes-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pes">🗂️ Event Sets</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent.</div>
      <div id="pes-delete-status" class="bf-status"></div>
      <label class="bf-label">Set IDs to delete (comma-separated)</label>
      <input type="text" id="pes-del-ids" placeholder="143, 144" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="pes-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="pes-delete-log"></div>
      <button class="bf-btn bf-danger" id="pes-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-pes", "screen-pes-create", "screen-pes-view", "screen-pes-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("pes-action-tpl").onclick = async () => {
    const btn = document.getElementById("pes-action-tpl"); btn.style.opacity = "0.6";
    const events = await fetchPaycodeEventsRef();
    downloadExcel("paycode_event_sets_template.xlsx", [
      { name: "Event_Sets", tabColor: "7C3AED", headers: ["set_id", "set_name", "set_description", "entry_id", "priority", "paycode_event_id"], rows: [], highlightCols: [1, 5] },
      { name: "Paycode_Events_Master", tabColor: "059669", headers: ["id", "name", "description", "paycode_id"], rows: events.map(e => [e.id, e.name || "", e.description || "", e.paycode?.id || ""]) }
    ]);
    btn.style.opacity = "1";
  };
  document.getElementById("pes-action-create").onclick = () => {
    Notifications.clearLog("pes-create-log"); AppState.cache.pes = null;
    document.getElementById("pes-submit").disabled = true;
    document.getElementById("pes-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    Router.go("screen-pes-create");
  };
  document.getElementById("pes-action-view").onclick = () => Router.go("screen-pes-view");
  document.getElementById("pes-action-delete").onclick = () => { Notifications.clearLog("pes-delete-log"); Router.go("screen-pes-delete"); };
  wireFileInput("pes-file", "pes-file-name", "pes-submit", "pes");

  document.getElementById("pes-submit").onclick = async () => {
    const btn = document.getElementById("pes-submit");
    const rows = AppState.cache.pes || [];
    Notifications.clearLog("pes-create-log");
    if (!rows.length) { Notifications.error("pes-create-status", "❌ No data found"); return; }

    const updateGroups = {}, createGroups = {};
    rows.forEach(row => {
      const setId = parseIntSafe(row["set_id"]);
      if (setId !== null) { if (!updateGroups[setId]) updateGroups[setId] = []; updateGroups[setId].push(row); }
      else { const setName = String(row["set_name"] || "").trim(); if (!setName) return; if (!createGroups[setName]) createGroups[setName] = []; createGroups[setName].push(row); }
    });
    const updateEntries = Object.entries(updateGroups), createEntries = Object.entries(createGroups);
    const total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error("pes-create-status", "❌ No valid groups found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("pes-c-prog");
    let s = 0, f = 0, done = 0;

    for (const [setId, group] of updateEntries) {
      const first = group[0];
      const payload = { id: parseInt(setId), name: String(first["set_name"] || "").trim(), description: String(first["set_description"] || "").trim() || String(first["set_name"] || "").trim(), entries: [] };
      const seen = new Set();
      group.forEach(row => {
        const entryId = parseIntSafe(row["entry_id"]); const priority = parseIntSafe(row["priority"]) || 1; const pcEventId = parseIntSafe(row["paycode_event_id"]);
        if (!pcEventId) return; const key = `${entryId}-${pcEventId}`; if (seen.has(key)) return; seen.add(key);
        const entry = { paycodeEvent: { id: pcEventId }, priority, overridable: false }; if (entryId !== null) entry.id = entryId;
        payload.entries.push(entry);
      });
      try {
        const r = await ApiTracker.fetch(`${BASE()}/${payload.id}`, { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Paycode Event Sets");
        if (r.ok) { Notifications.log("pes-create-log", `✅ Updated: ${payload.name} (${payload.entries.length} entries)`, "ok"); s++; Audit.onDbOp("updated", 1); }
        else { Notifications.log("pes-create-log", `❌ Failed update: ${payload.name} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("pes-create-log", `❌ Error: ${payload.name} — ${e.message}`, "fail"); f++; }
      done++; Notifications.progress.set("pes-c-bar", (done / total) * 100);
    }
    for (const [setName, group] of createEntries) {
      const first = group[0];
      const payload = { name: setName, description: String(first["set_description"] || "").trim() || setName, entries: [] };
      const seen = new Set();
      group.forEach(row => {
        const priority = parseIntSafe(row["priority"]) || 1; const pcEventId = parseIntSafe(row["paycode_event_id"]);
        if (!pcEventId || seen.has(pcEventId)) return; seen.add(pcEventId);
        payload.entries.push({ paycodeEvent: { id: pcEventId }, priority, overridable: false });
      });
      try {
        const r = await ApiTracker.fetch(`${BASE()}/`, { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Paycode Event Sets");
        if (r.ok) { Notifications.log("pes-create-log", `✅ Created: ${payload.name} (${payload.entries.length} entries)`, "ok"); s++; Audit.onDbOp("created", 1); }
        else { Notifications.log("pes-create-log", `❌ Failed create: ${payload.name} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("pes-create-log", `❌ Error: ${payload.name} — ${e.message}`, "fail"); f++; }
      done++; Notifications.progress.set("pes-c-bar", (done / total) * 100);
    }

    Notifications.log("pes-create-log", `━━━━━━━━━━━━━━━━━━`, "info");
    Notifications.log("pes-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("pes-create-status", `Done — ${s} success, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit Paycode Event Sets");
    Notifications.progress.hide("pes-c-prog");
  };

  document.getElementById("pes-do-delete").onclick = async () => {
    if (!document.getElementById("pes-confirm").checked) { Notifications.error("pes-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("pes-del-ids").value.split(",").map(s => s.trim()).filter(s => !isNaN(s) && s !== "");
    if (!ids.length) { Notifications.error("pes-delete-status", "❌ No valid IDs"); return; }
    const btn = document.getElementById("pes-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("pes-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Paycode Event Sets");
        if (r.status === 200 || r.status === 204) { Notifications.log("pes-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("pes-delete-log", `❌ Failed: ${id}`, "fail"); f++; }
      } catch (e) { Notifications.log("pes-delete-log", `❌ Error: ${id}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("pes-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };

  document.getElementById("pes-fetch").onclick = async () => {
    const btn = document.getElementById("pes-fetch");
    Notifications.loading(btn, "Connecting to server...");
    Notifications.progress.show("pes-v-prog");
    try {
      Notifications.info("pes-view-status", "⏳ Fetching records..."); Notifications.progress.set("pes-v-bar", 25);
      const r = await ApiTracker.fetch(`${BASE()}/?projection=FULL`, { headers: apiH() }, "Paycode Event Sets");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      AppState.cache.pesView = await r.json();
      Notifications.info("pes-view-status", `⏳ Processing ${AppState.cache.pesView.length} set(s)...`); Notifications.progress.set("pes-v-bar", 60);
      const rows = [];
      (AppState.cache.pesView || []).forEach(set => (set.entries || []).forEach(entry => {
        const pe = entry.paycodeEvent || {};
        rows.push([set.id, set.name || "", set.description || "", pe.id || "", entry.priority || "", entry.id || "", pe.name || "", pe.description || "", pe.paycode?.id || "", pe.paycode?.code || ""]);
      }));
      if (!rows.length) { Notifications.info("pes-view-status", "ℹ️ No records available to download."); return; }
      Notifications.info("pes-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("pes-v-bar", 85);
      downloadExcel("paycode_event_sets_existing.xlsx", [{
        name: "Event_Sets", tabColor: "7C3AED",
        headers: ["id", "name", "description", "paycode_event_id", "priority", "entry_id", "paycode_event_name", "paycode_event_description", "paycode_id", "paycode_code"],
        rows
      }]);
      Notifications.progress.set("pes-v-bar", 100);
      Notifications.success("pes-view-status", `✅ Download complete — ${AppState.cache.pesView.length} set(s)`);
    } catch (e) {
      Notifications.error("pes-view-status", `❌ ${e.message}`); Notifications.progress.set("pes-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Event Sets");
      Notifications.progress.hide("pes-v-prog", 2000);
    }
  };
}
