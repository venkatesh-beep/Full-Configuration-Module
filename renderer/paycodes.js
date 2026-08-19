/* =========================================================
 * paycodes.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/paycodes.js — BeeForce Configuration Portal
// Owns: screen-pay, screen-pay-create, screen-pay-view, screen-pay-delete
// GET    /api/attendance/paycodes?projection=FULL
// GET    /api/attendance/paycode_attributes
// POST   /api/attendance/paycodes                   (create)
// PUT    /api/attendance/paycodes/{id}               (update)
// DELETE /api/attendance/paycodes/{id}
// Exports: init(context)
// =========================================================

const PAY_VIEW_HEADERS = [
  "id", "code", "description", "inactive", "schedule", "absence",
  "validateWithPaycodeEvent", "exception", "historical", "optionalHoliday",
  "presentDays", "lopDays", "leaveDays", "woDays", "holDays", "payableDays", "otHours",
  "DAY_FLAG", "PAYDED_FLG", "linkTimeOffInTimeCard", "linkRegularizeInTimeCard",
  "futureDays", "HISTORICAL_PAYDED_FLG", "HOLIDAY_OT_GROUP",
  "Linked Paycode", "Linked Paycode Code"
];
const PAY_BASE_UPLOAD_HEADERS = [
  "id (blank=create)", "code", "description", "inactive", "schedule", "absence",
  "validateWithPaycodeEvent", "exception", "historical", "optionalHoliday",
  "presentDays", "lopDays", "leaveDays", "woDays", "holDays", "payableDays", "otHours",
  "linkTimeOffInTimeCard", "linkRegularizeInTimeCard",
  "futureDays", "pastDays",
  "Linked Paycode (id)"
];
const ATTR_INSERT_IDX = 17;
const PAY_INPUT_COLS = [1, 2];

function payUploadHeaders(attrs) {
  if (!attrs || !attrs.length) return PAY_BASE_UPLOAD_HEADERS;
  const attrCols = [...attrs].sort((a, b) => (a.sequence || 99) - (b.sequence || 99)).map(a => a.name);
  return [...PAY_BASE_UPLOAD_HEADERS.slice(0, ATTR_INSERT_IDX), ...attrCols, ...PAY_BASE_UPLOAD_HEADERS.slice(ATTR_INSERT_IDX)];
}

function payFlatten(p) {
  const ts = v => (v === null || v === undefined) ? "" : typeof v === "boolean" ? (v ? "TRUE" : "FALSE") : String(v);
  const props = p.properties || {};
  const linked = p.linkedPaycode || {};
  return [
    ts(p.id), ts(p.code), ts(p.description),
    ts(p.inactive), ts(p.schedule), ts(p.absence),
    ts(p.validateWithPaycodeEvent), ts(p.exception), ts(p.historical), ts(p.optionalHoliday),
    ts(p.presentDays ?? 0), ts(p.lopDays ?? 0), ts(p.leaveDays ?? 0),
    ts(p.woDays ?? 0), ts(p.holDays ?? 0), ts(p.payableDays ?? 0), ts(p.otHours ?? 0),
    ts(props.DAY_FLAG || ""), ts(props.PAYDED_FLG || ""),
    ts(p.linkTimeOffInTimeCard), ts(p.linkRegularizeInTimeCard),
    ts(p.futureDays ?? p.pastDays ?? ""),
    ts(props.HISTORICAL_PAYDED_FLG || ""), ts(props.HOLIDAY_OT_GROUP || ""),
    ts(linked.id || ""), ts(linked.code || "")
  ];
}

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const PAY_BASE = () => `${AppState.BASE_URL}/api/attendance/paycodes`;
  const PAY_ATTR = () => `${AppState.BASE_URL}/api/attendance/paycode_attributes`;

  async function payFetchAll() {
    const r = await ApiTracker.fetch(`${PAY_BASE()}?projection=FULL`, { headers: apiH() }, "Paycodes");
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
    const raw = await r.json();
    return Array.isArray(raw) ? raw : (raw.content || raw.data || []);
  }
  async function payFetchAttrs() {
    try { const r = await ApiTracker.fetch(PAY_ATTR(), { headers: apiH() }, "Paycodes"); return r.ok ? await r.json() : []; }
    catch (e) { return []; }
  }
  function payBuildPayload(row, attrs) {
    const col = (name) => {
      const n = name.toLowerCase().replace(/[^a-z0-9]/g, "");
      const k = Object.keys(row).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, "") === n);
      return k ? String(row[k] || "").trim() : "";
    };
    const toBool = v => ["true", "1", "yes"].includes(String(v || "").toLowerCase().trim());
    const toNum = (v, d = 0) => { const n = parseFloat(v); return isNaN(n) ? d : n; };

    const payload = {
      code: col("code"), description: col("description"),
      inactive: toBool(col("inactive")), schedule: toBool(col("schedule")), absence: toBool(col("absence")),
      validateWithPaycodeEvent: toBool(col("validateWithPaycodeEvent")), exception: toBool(col("exception")),
      historical: toBool(col("historical")), optionalHoliday: toBool(col("optionalHoliday")),
      presentDays: toNum(col("presentDays")), lopDays: toNum(col("lopDays")), leaveDays: toNum(col("leaveDays")),
      woDays: toNum(col("woDays")), holDays: toNum(col("holDays")), payableDays: toNum(col("payableDays")), otHours: toNum(col("otHours")),
      linkTimeOffInTimeCard: toBool(col("linkTimeOffInTimeCard")), linkRegularizeInTimeCard: toBool(col("linkRegularizeInTimeCard")),
      properties: {}
    };
    ["DAY_FLAG", "PAYDED_FLG", "HISTORICAL_PAYDED_FLG", "HOLIDAY_OT_GROUP"].forEach(name => { const v = col(name); if (v) payload.properties[name] = v; });
    (attrs || []).forEach(a => { const v = col(a.name); if (v) payload.properties[a.name] = v; });
    if (!Object.keys(payload.properties).length) delete payload.properties;

    const futureDays = parseIntSafe(col("futureDays")); if (futureDays !== null) payload.futureDays = futureDays;
    const pastDays = parseIntSafe(col("pastDays")); if (pastDays !== null) payload.pastDays = pastDays;
    const linkedId = parseIntSafe(col("Linked Paycode (id)") || col("Linked Paycode") || col("LinkedPaycode") || col("linked_paycode_id"));
    if (linkedId !== null) payload.linkedPaycode = { id: linkedId };
    return payload;
  }

  if (!document.getElementById("screen-pay")) {
    const main = document.createElement("div");
    main.id = "screen-pay"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🎯 Paycodes</span></div>
      <div class="bf-module-header"><div class="mh-icon">🎯</div><div><div class="mh-title">Paycodes</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="pay-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload cols + existing paycodes + paycode attributes</div></div>
        <div class="bf-action-card" id="pay-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Blank id = create (POST) · fill id = update (PUT)</div></div>
        <div class="bf-action-card" id="pay-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Fetch all paycodes (projection=FULL) and download</div></div>
        <div class="bf-action-card" id="pay-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete paycodes by comma-separated IDs</div></div>
      </div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-pay-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pay">🎯 Paycodes</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>
      <div class="bf-info-box">Leave <b>id</b> blank to create (POST). Fill <b>id</b> to update (PUT).<br>Attribute columns (DAY_FLAG, PAYDED_FLG etc.) go into the <code>properties</code> object.</div>
      <div id="pay-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="pay-file"><span id="pay-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="pay-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="pay-c-prog"><div class="bf-pb" id="pay-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="pay-create-log"></div>
      <button class="bf-btn bf-success" id="pay-submit" disabled>🚀 Create / Update Paycodes</button>
      <button class="bf-btn bf-outline" id="pay-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="pay-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-pay-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pay">🎯 Paycodes</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>
      <div id="pay-view-status" class="bf-status"></div>
      <div class="bf-progress" id="pay-v-prog" style="display:none"><div class="bf-pb" id="pay-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="pay-fetch">⬇️ Download Paycodes</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-pay-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pay">🎯 Paycodes</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>
      <div id="pay-delete-status" class="bf-status"></div>
      <label class="bf-label">Paycode IDs to delete (comma-separated)</label>
      <input type="text" id="pay-del-ids" placeholder="392, 393, 394" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="pay-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="pay-delete-log"></div>
      <button class="bf-btn bf-danger" id="pay-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-pay", "screen-pay-create", "screen-pay-view", "screen-pay-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("pay-action-tpl").onclick = async () => {
    const btn = document.getElementById("pay-action-tpl"); btn.style.opacity = "0.6";
    const [payRes, attrRes] = await Promise.allSettled([payFetchAll().catch(() => []), payFetchAttrs()]);
    const existing = payRes.status === "fulfilled" ? payRes.value : [];
    const attrs = attrRes.status === "fulfilled" ? attrRes.value : [];
    const uploadHeaders = payUploadHeaders(attrs);
    const existRows = existing.map(p => payFlatten(p));
    const sheets = [
      { name: "Paycodes_Upload", tabColor: "1D4ED8", headers: uploadHeaders, rows: [], highlightCols: PAY_INPUT_COLS },
      { name: "Existing_Paycodes_Ref", tabColor: "7C3AED", headers: PAY_VIEW_HEADERS, rows: existRows }
    ];
    if (attrs.length) {
      sheets.push({ name: "Paycode_Attributes", tabColor: "059669", headers: ["sequence", "name", "label", "type", "required"], rows: attrs.map(a => [a.sequence, a.name, a.label, a.type, a.required ? "TRUE" : "FALSE"]) });
    }
    downloadExcel("paycodes_template.xlsx", sheets);
    btn.style.opacity = "1";
  };

  document.getElementById("pay-action-create").onclick = () => {
    Notifications.clearLog("pay-create-log"); AppState.cache.pay = null; AppState.cache.paySuccess = []; AppState.cache.payFailed = [];
    document.getElementById("pay-submit").disabled = true;
    document.getElementById("pay-dl-success").style.display = "none";
    document.getElementById("pay-dl-failed").style.display = "none";
    Router.go("screen-pay-create");
  };
  document.getElementById("pay-action-view").onclick = () => Router.go("screen-pay-view");
  document.getElementById("pay-action-delete").onclick = () => { Notifications.clearLog("pay-delete-log"); Router.go("screen-pay-delete"); };

  wireFileInput("pay-file", "pay-file-name", "pay-submit", "pay");

  document.getElementById("pay-dl-success").onclick = () => {
    downloadExcel("pay_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["id", "code", "description", "action"], rows: (AppState.cache.paySuccess || []).map(r => [r.id || "", r.code, r.description, r.action]) }]);
  };
  document.getElementById("pay-dl-failed").onclick = () => {
    downloadExcel("pay_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["code", "description", "http_status", "error"], rows: (AppState.cache.payFailed || []).map(r => [r.code, r.description, r.status || "", r.error || ""]) }]);
  };

  document.getElementById("pay-submit").onclick = async () => {
    const btn = document.getElementById("pay-submit");
    const rows = AppState.cache.pay || [];
    Notifications.clearLog("pay-create-log");
    document.getElementById("pay-dl-success").style.display = "none";
    document.getElementById("pay-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("pay-create-status", "❌ No data"); return; }

    const attrs = await payFetchAttrs();

    Notifications.loading(btn, `Processing 0/${rows.length}...`);
    Notifications.progress.show("pay-c-prog");
    AppState.cache.paySuccess = []; AppState.cache.payFailed = [];
    let s = 0, f = 0;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const col = (name) => {
        const n = name.toLowerCase().replace(/[^a-z0-9]/g, "");
        const k = Object.keys(row).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, "") === n);
        return k ? String(row[k] || "").trim() : "";
      };
      const rawId = col("id") || col("id blankcreate");
      const existingId = parseIntSafe(rawId);
      const isUpdate = existingId !== null;
      const payload = payBuildPayload(row, attrs);
      if (isUpdate) payload.id = existingId;
      if (!payload.code) { Notifications.log("pay-create-log", `⚠️ Row ${i + 2}: 'code' is required — skipped`, "fail"); f++; continue; }

      try {
        const url = isUpdate ? `${PAY_BASE()}/${existingId}` : `${PAY_BASE()}`;
        const method = isUpdate ? "PUT" : "POST";
        const r = await ApiTracker.fetch(url, { method, headers: apiH(), body: JSON.stringify(payload) }, "Paycodes");
        const body = await r.text();
        if (r.ok) {
          let rid = existingId || ""; try { rid = JSON.parse(body).id || rid; } catch (e) {}
          Notifications.log("pay-create-log", `✅ ${isUpdate ? "Updated" : "Created"}: ${payload.code} — ${payload.description}`, "ok");
          AppState.cache.paySuccess.push({ id: rid, code: payload.code, description: payload.description, action: isUpdate ? "Updated" : "Created" });
          Audit.onDbOp(isUpdate ? "updated" : "created", 1);
          s++;
        } else {
          const err = parseApiError(body);
          Notifications.log("pay-create-log", `❌ Failed: ${payload.code} — ${err}`, "fail");
          AppState.cache.payFailed.push({ code: payload.code, description: payload.description, status: r.status, error: err });
          f++;
        }
      } catch (e) {
        Notifications.log("pay-create-log", `❌ Error: ${payload.code} — ${e.message}`, "fail");
        AppState.cache.payFailed.push({ code: payload.code || "", description: payload.description || "", status: "NET", error: e.message });
        f++;
      }
      Notifications.progress.set("pay-c-bar", ((i + 1) / rows.length) * 100);
      Notifications.loading(btn, `Processing ${i + 1}/${rows.length}...`);
    }

    Notifications.log("pay-create-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("pay-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("pay-create-status", `Done — ${s} processed, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Create / Update Paycodes");
    Notifications.progress.hide("pay-c-prog");
    if (AppState.cache.paySuccess.length) document.getElementById("pay-dl-success").style.display = "block";
    if (AppState.cache.payFailed.length) document.getElementById("pay-dl-failed").style.display = "block";
  };

  document.getElementById("pay-fetch").onclick = async () => {
    const btn = document.getElementById("pay-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("pay-v-prog");
    try {
      Notifications.info("pay-view-status", "⏳ Fetching paycodes..."); Notifications.progress.set("pay-v-bar", 25);
      const list = await payFetchAll();
      if (!list.length) { Notifications.info("pay-view-status", "ℹ️ No paycodes found."); return; }
      Notifications.info("pay-view-status", `⏳ Processing ${list.length} paycode(s)...`); Notifications.progress.set("pay-v-bar", 70);
      const rows = list.map(p => payFlatten(p));
      Notifications.info("pay-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("pay-v-bar", 90);
      downloadExcel(`paycodes_${new Date().toISOString().slice(0, 10)}.xlsx`, [{ name: "Paycodes", tabColor: "1D4ED8", headers: PAY_VIEW_HEADERS, rows }]);
      Notifications.progress.set("pay-v-bar", 100);
      Notifications.success("pay-view-status", `✅ Download complete — ${list.length} paycode(s)`);
    } catch (e) {
      Notifications.error("pay-view-status", `❌ ${e.message}`); Notifications.progress.set("pay-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Paycodes");
      Notifications.progress.hide("pay-v-prog", 2500);
    }
  };

  document.getElementById("pay-do-delete").onclick = async () => {
    if (!document.getElementById("pay-confirm").checked) { Notifications.error("pay-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("pay-del-ids").value.split(",").map(s => s.trim()).filter(s => s !== "");
    if (!ids.length) { Notifications.error("pay-delete-status", "❌ No IDs"); return; }
    const btn = document.getElementById("pay-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("pay-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${PAY_BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Paycodes");
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("pay-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("pay-delete-log", `❌ Failed: ${id} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("pay-delete-log", `❌ Error: ${id} — ${e.message}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("pay-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };
}
