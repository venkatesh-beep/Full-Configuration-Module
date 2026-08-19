/* =========================================================
 * paycode-combinations.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/paycode-combinations.js — BeeForce Configuration Portal
// Owns: screen-pco, screen-pco-create, screen-pco-view, screen-pco-delete
// GET/POST/PUT/DELETE /api/attendance/paycode_combinations
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, Notifications, Router, Audit, ApiTracker, fetchPaycodesRef, modal } = ctx;
  const BASE = () => `${AppState.BASE_URL}/api/attendance/paycode_combinations`;

  if (!document.getElementById("screen-pco")) {
    const main = document.createElement("div");
    main.id = "screen-pco"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🔗 Combinations</span></div>
      <div class="bf-module-header"><div class="mh-icon">🔗</div><div><div class="mh-title">Paycode Combinations</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="pco-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div></div>
        <div class="bf-action-card" id="pco-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Submit</div></div>
        <div class="bf-action-card" id="pco-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div></div>
        <div class="bf-action-card" id="pco-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div></div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-pco-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pco">🔗 Combinations</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Submit</span></div>
      <div class="bf-info-box">Leave <b>id</b> blank to create, fill to update.</div>
      <div id="pco-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="pco-file"><span id="pco-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="pco-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="pco-c-prog"><div class="bf-pb" id="pco-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="pco-create-log"></div>
      <button class="bf-btn bf-success" id="pco-submit" disabled>🚀 Submit Combinations</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-pco-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pco">🔗 Combinations</span><span class="bc-sep">›</span><span class="bc-cur">View</span></div>
      <div id="pco-view-status" class="bf-status"></div>
      <div class="bf-progress" id="pco-v-prog" style="display:none"><div class="bf-pb" id="pco-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="pco-fetch">⬇️ Download Combinations</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-pco-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pco">🔗 Combinations</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent.</div>
      <div id="pco-delete-status" class="bf-status"></div>
      <label class="bf-label">Combination IDs (comma-separated)</label>
      <input type="text" id="pco-del-ids" placeholder="924, 925" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="pco-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="pco-delete-log"></div>
      <button class="bf-btn bf-danger" id="pco-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-pco", "screen-pco-create", "screen-pco-view", "screen-pco-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("pco-action-tpl").onclick = async () => {
    const btn = document.getElementById("pco-action-tpl"); btn.style.opacity = "0.6";
    const pcs = await fetchPaycodesRef();
    downloadExcel("paycode_combinations_template.xlsx", [
      { name: "Paycode_Combinations", tabColor: "D97706", headers: ["id", "firstPaycode", "secondPaycode", "combinedPaycode", "inactive"], rows: [], highlightCols: [1, 2, 3] },
      { name: "Available_Paycodes", tabColor: "059669", headers: ["id", "code", "description"], rows: pcs.map(p => [p.id, p.code || "", p.description || ""]) }
    ]);
    btn.style.opacity = "1";
  };
  document.getElementById("pco-action-create").onclick = () => {
    Notifications.clearLog("pco-create-log"); AppState.cache.pco = null;
    document.getElementById("pco-submit").disabled = true;
    document.getElementById("pco-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    Router.go("screen-pco-create");
  };
  document.getElementById("pco-action-view").onclick = () => Router.go("screen-pco-view");
  document.getElementById("pco-action-delete").onclick = () => { Notifications.clearLog("pco-delete-log"); Router.go("screen-pco-delete"); };
  wireFileInput("pco-file", "pco-file-name", "pco-submit", "pco");

  document.getElementById("pco-submit").onclick = async () => {
    const btn = document.getElementById("pco-submit");
    const rows = AppState.cache.pco || [];
    Notifications.clearLog("pco-create-log");
    if (!rows.length) { Notifications.error("pco-create-status", "❌ No data found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("pco-c-prog");
    let s = 0, f = 0;
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      try {
        const firstPc = parseInt(row["firstPaycode"]), secondPc = parseInt(row["secondPaycode"]), combinedPc = parseInt(row["combinedPaycode"]);
        const inactive = String(row["inactive"]).toLowerCase() === "true";
        const rawId = String(row["id"] || "").trim();
        const payload = { firstPaycode: { id: firstPc }, secondPaycode: { id: secondPc }, combinedPaycode: { id: combinedPc }, inactive };
        let r;
        if (rawId && !isNaN(rawId)) {
          payload.id = parseInt(rawId);
          r = await ApiTracker.fetch(`${BASE()}/${rawId}`, { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Paycode Combinations");
        } else {
          r = await ApiTracker.fetch(`${BASE()}`, { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Paycode Combinations");
        }
        if (r.ok) {
          Notifications.log("pco-create-log", `✅ ${rawId ? "Updated" : "Created"}: ${firstPc}+${secondPc}→${combinedPc}`, "ok");
          s++; Audit.onDbOp(rawId ? "updated" : "created", 1);
        } else {
          Notifications.log("pco-create-log", `❌ Failed: row ${i + 1} — ${parseApiError(await r.text())}`, "fail"); f++;
        }
      } catch (e) { Notifications.log("pco-create-log", `❌ Error: row ${i + 1} — ${e.message}`, "fail"); f++; }
      Notifications.progress.set("pco-c-bar", ((i + 1) / rows.length) * 100);
    }
    Notifications.log("pco-create-log", `━━━━━━━━━━━━━━━━━━`, "info");
    Notifications.log("pco-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("pco-create-status", `Done — ${s} success, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit Combinations");
    Notifications.progress.hide("pco-c-prog");
  };

  document.getElementById("pco-do-delete").onclick = async () => {
    if (!document.getElementById("pco-confirm").checked) { Notifications.error("pco-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("pco-del-ids").value.split(",").map(s => s.trim()).filter(s => !isNaN(s) && s !== "");
    if (!ids.length) { Notifications.error("pco-delete-status", "❌ No valid IDs"); return; }
    const btn = document.getElementById("pco-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("pco-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Paycode Combinations");
        if (r.status === 200 || r.status === 204) { Notifications.log("pco-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("pco-delete-log", `❌ Failed: ${id}`, "fail"); f++; }
      } catch (e) { Notifications.log("pco-delete-log", `❌ Error: ${id}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("pco-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };

  document.getElementById("pco-fetch").onclick = async () => {
    const btn = document.getElementById("pco-fetch");
    Notifications.loading(btn, "Connecting to server...");
    Notifications.progress.show("pco-v-prog");
    try {
      Notifications.info("pco-view-status", "⏳ Fetching records..."); Notifications.progress.set("pco-v-bar", 25);
      const r = await ApiTracker.fetch(`${BASE()}`, { headers: apiH() }, "Paycode Combinations");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
      AppState.cache.pcoView = await r.json();
      Notifications.info("pco-view-status", `⏳ Processing ${AppState.cache.pcoView.length} combination(s)...`); Notifications.progress.set("pco-v-bar", 60);
      const rows = (AppState.cache.pcoView || []).map(c => [c.id, c.firstPaycode?.id, c.secondPaycode?.id, c.combinedPaycode?.id, c.inactive]);
      if (!rows.length) { Notifications.info("pco-view-status", "ℹ️ No records available to download."); return; }
      Notifications.info("pco-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("pco-v-bar", 85);
      downloadExcel("paycode_combinations_existing.xlsx", [{ name: "Combinations", tabColor: "D97706", headers: ["id", "firstPaycode", "secondPaycode", "combinedPaycode", "inactive"], rows }]);
      Notifications.progress.set("pco-v-bar", 100);
      Notifications.success("pco-view-status", `✅ Download complete — ${AppState.cache.pcoView.length} combination(s)`);
    } catch (e) {
      Notifications.error("pco-view-status", `❌ ${e.message}`); Notifications.progress.set("pco-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Combinations");
      Notifications.progress.hide("pco-v-prog", 2000);
    }
  };
}
