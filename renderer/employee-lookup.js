/* =========================================================
 * employee-lookup.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/employee-lookup.js — BeeForce Configuration Portal
// Owns: screen-el
// Endpoints:
//   GET  /api/attendance/employee_lookup_table
//   POST /api/attendance/employee_lookup_table/action   {action:"SAVE", table:{...}}
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, formatValue, parseApiError, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const prefix = "el";
  const entityType = "EMPLOYEE";
  const getUrl = () => `${AppState.BASE_URL}/api/attendance/employee_lookup_table`;
  const postUrl = () => `${AppState.BASE_URL}/api/attendance/employee_lookup_table/action`;

  if (!document.getElementById("screen-el")) {
    const main = document.createElement("div");
    main.id = "screen-el"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">👤 Employee Lookup</span></div>
      <div class="bf-module-header"><div class="mh-icon">👤</div><div><div class="mh-title">Employee Lookup Table</div><div class="mh-sub">Download · Upload</div></div></div>
      <div id="el-status" class="bf-status"></div>
      <button class="bf-btn bf-primary" id="el-download">⬇️ Download Existing Data</button>
      <div class="bf-divider"></div>
      <div class="bf-info-box">Red highlighted columns are <b>INPUT (mandatory)</b> fields.</div>
      <label class="bf-file-label" for="el-file"><span id="el-file-name">📂 Click to select filled file (.xlsx)</span></label>
      <input type="file" id="el-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="el-prog"><div class="bf-pb" id="el-bar" style="width:0%"></div></div>
      <div class="bf-log" id="el-log"></div>
      <button class="bf-btn bf-success" id="el-submit" disabled>🚀 Validate & Upload</button>`;
    modal.appendChild(main);

    Router.register("screen-el");
    Router.wireDataGoLinks(main);
    main.querySelectorAll("input,textarea").forEach(inp =>
      ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
    );
  }

  async function fetchLookupTable(url) {
    const r = await ApiTracker.fetch(url, { headers: apiH() }, "Employee Lookup");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const raw = await r.json();
    const headersMeta = (raw.headers || []).sort((a, b) => (a.sequence || 999) - (b.sequence || 999));
    return { headersMeta, data: raw.content || raw.data || [] };
  }

  document.getElementById(`${prefix}-download`).onclick = async () => {
    const btn = document.getElementById(`${prefix}-download`);
    Notifications.loading(btn, "Fetching...");
    try {
      const { headersMeta, data } = await fetchLookupTable(getUrl());
      const columns = headersMeta.map(h => h.data);
      const inputColIdx = headersMeta.map((h, i) => (h.type === "INPUT" ? i : -1)).filter(i => i >= 0);
      const rows = data.map(row => columns.map(c => formatValue(row[c])));
      downloadExcel(`employee_lookup_data.xlsx`, [{ name: "Existing_Data", tabColor: "1D4ED8", headers: columns, rows, highlightCols: inputColIdx }]);
      AppState.cache[`${prefix}HeadersMeta`] = headersMeta;
      Notifications.success(`${prefix}-status`, `✅ ${data.length} records downloaded (INPUT columns highlighted red)`);
    } catch (e) {
      Notifications.error(`${prefix}-status`, `❌ ${e.message}`);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Existing Data");
    }
  };

  wireFileInput(`${prefix}-file`, `${prefix}-file-name`, `${prefix}-submit`, prefix);

  document.getElementById(`${prefix}-submit`).onclick = async () => {
    const btn = document.getElementById(`${prefix}-submit`);
    const rows = AppState.cache[prefix] || [];
    Notifications.clearLog(`${prefix}-log`);
    if (!rows.length) { Notifications.error(`${prefix}-status`, "❌ No data found"); return; }

    Notifications.loading(btn, "Validating...");
    let headersMeta = AppState.cache[`${prefix}HeadersMeta`];
    if (!headersMeta) {
      try { const lt = await fetchLookupTable(getUrl()); headersMeta = lt.headersMeta; }
      catch (e) {
        Notifications.error(`${prefix}-status`, `❌ Failed to fetch headers: ${e.message}`);
        Notifications.doneLoading(btn, "🚀 Validate & Upload"); return;
      }
    }
    const inputColumns = headersMeta.filter(h => h.type === "INPUT").map(h => h.data);
    const allColumns = headersMeta.map(h => h.data);
    let validationErrors = [], dataRows = [];
    rows.forEach((row, idx) => {
      const excelRow = idx + 2; let rowHasError = false;
      for (const col of inputColumns) {
        if (!(col in row) || formatValue(row[col]) === "") {
          validationErrors.push({ Row: excelRow, Field: col, Error: "INPUT field cannot be empty" });
          rowHasError = true;
        }
      }
      if (rowHasError) return;
      const record = {};
      for (const col of allColumns) { if (col in row) { const value = formatValue(row[col]); if (value !== "") record[col] = value; } }
      if (Object.keys(record).length) dataRows.push(record);
    });

    if (validationErrors.length) {
      Notifications.log(`${prefix}-log`, `❌ Validation failed:`, "fail");
      validationErrors.forEach(e => {
        Notifications.log(`${prefix}-log`, `⚠️ Row ${e.Row} — "${e.Field}": ${e.Error}`, "fail");
        Audit.onValidationError(`Employee Lookup row ${e.Row} "${e.Field}": ${e.Error}`);
      });
      Notifications.error(`${prefix}-status`, "❌ Validation failed");
      Notifications.doneLoading(btn, "🚀 Validate & Upload");
      return;
    }
    if (!dataRows.length) { Notifications.error(`${prefix}-status`, "No valid rows to upload"); Notifications.doneLoading(btn, "🚀 Validate & Upload"); return; }

    Notifications.loading(btn, `Uploading ${dataRows.length} row(s)...`);
    Notifications.progress.show(`${prefix}-prog`);
    Notifications.progress.set(`${prefix}-bar`, 30);
    try {
      const r = await ApiTracker.fetch(postUrl(), {
        method: "POST", headers: apiH(),
        body: JSON.stringify({ action: "SAVE", table: { entityType, headers: headersMeta, data: dataRows } })
      }, "Employee Lookup");
      Notifications.progress.set(`${prefix}-bar`, 100);
      if (r.status === 200 || r.status === 201) {
        Notifications.log(`${prefix}-log`, `✅ ${dataRows.length} row(s) uploaded`, "ok");
        Notifications.success(`${prefix}-status`, "✅ Lookup Table updated successfully");
        Audit.onDbOp("updated", dataRows.length);
      } else {
        const errText = await r.text();
        Notifications.log(`${prefix}-log`, `❌ ${parseApiError(errText)}`, "fail");
        Notifications.error(`${prefix}-status`, "❌ Upload failed");
      }
    } catch (e) {
      Notifications.log(`${prefix}-log`, `❌ Error: ${e.message}`, "fail");
      Notifications.error(`${prefix}-status`, "❌ Upload failed");
    }
    Notifications.doneLoading(btn, "🚀 Validate & Upload");
    Notifications.progress.hide(`${prefix}-prog`);
  };
}
