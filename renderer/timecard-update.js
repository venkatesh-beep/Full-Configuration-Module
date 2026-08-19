/* =========================================================
 * timecard-update.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/timecard-update.js — BeeForce Configuration Portal
// Owns: screen-tc, screen-tc-upload
// GET  /api/attendance/timecards   (one per employee, concurrent)
// POST /api/attendance/timecards   (batch per date, individual fallback)
// Every HTTP 200/201 from POST is re-verified with a follow-up GET
// before being counted as a real success (matches legacy v3 behavior).
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, fetchPaycodesRef, modal } = ctx;

  const TC_GET_BASE  = () => `${AppState.BASE_URL}/api/attendance/timecards`;
  const TC_POST_BASE = () => `${AppState.BASE_URL}/api/attendance/timecards`;
  const TC_ATTR = "attendancePunches(organizationLocation|shiftTemplate),schedule(shiftTemplate)";
  const TC_MAX_RETRIES = 3;
  const TC_BACKOFF_MS = 2000;
  const tcTransient = s => s === 429 || (s >= 500 && s < 600);
  const tcSleep = ms => new Promise(r => setTimeout(r, ms));

  function tcNormalizeDate(val) {
    if (!val) return "";
    const s = String(val).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    const long = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (long) return `${long[3]}-${long[1].padStart(2, "0")}-${long[2].padStart(2, "0")}`;
    const short = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2})$/);
    if (short) return `${2000 + parseInt(short[3])}-${short[1].padStart(2, "0")}-${short[2].padStart(2, "0")}`;
    try { const d = new Date(s); if (!isNaN(d)) return d.toISOString().slice(0, 10); } catch (e) {}
    return s;
  }

  // ── Inject screens ──────────────────────────────────────
  if (!document.getElementById("screen-tc")) {
    const main = document.createElement("div");
    main.id = "screen-tc"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🕐 Timecard Update</span></div>
      <div class="bf-module-header"><div class="mh-icon">🕐</div><div><div class="mh-title">Timecard Update</div><div class="mh-sub">Concurrent GETs · Batch POST · Verification GET · Individual fallback</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="tc-action-tpl">
          <div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div>
          <div class="ac-desc">Sheet 1: input columns · Sheet 2: paycodes master</div>
        </div>
        <div class="bf-action-card" id="tc-action-upload">
          <div class="ac-icon">📤</div><div class="ac-name">Upload & Update</div>
          <div class="ac-desc">Groups by date, fetches IDs concurrently, posts batch per date</div>
        </div>
      </div>`;
    modal.appendChild(main);

    const upload = document.createElement("div");
    upload.id = "screen-tc-upload"; upload.style.display = "none";
    upload.innerHTML = `
      <div class="bf-breadcrumb">
        <span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span>
        <span class="bc-link" data-go="screen-tc">🕐 Timecard Update</span><span class="bc-sep">›</span>
        <span class="bc-cur">Upload & Update</span>
      </div>
      <div class="bf-info-box">
        Required columns: <b>externalNumber</b>, <b>attendanceDate</b>, <b>paycode_id</b>.<br>
        Dates are auto-converted (accepts YYYY-MM-DD, MM/DD/YYYY, M/D/YY).<br>
        Employee IDs and versions are fetched concurrently before posting.
      </div>
      <div id="tc-status" class="bf-status"></div>
      <label class="bf-file-label" for="tc-file"><span id="tc-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="tc-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <label style="display:flex;align-items:center;gap:8px;font-size:12px;color:#6B7280;margin-bottom:12px;cursor:pointer;">
        <input type="checkbox" id="tc-debug" style="width:auto;margin:0;" />
        <span>🔍 Debug mode (print full GET URL and headers before each request)</span>
      </label>
      <div class="bf-progress" id="tc-prog"><div class="bf-pb" id="tc-bar" style="width:0%"></div></div>
      <div class="bf-log" id="tc-log"></div>
      <button class="bf-btn bf-success" id="tc-submit" disabled>🚀 Fetch & Update Timecards</button>
      <button class="bf-btn bf-outline" id="tc-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="tc-dl-failed" style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(upload);

    Router.register("screen-tc", "screen-tc-upload");
    [main, upload].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  // ── Download Template ────────────────────────────────────
  document.getElementById("tc-action-tpl").onclick = async () => {
    const btn = document.getElementById("tc-action-tpl"); btn.style.opacity = "0.6";
    const pcs = await fetchPaycodesRef();
    downloadExcel("timecard_update_template.xlsx", [
      { name: "Timecard_Update", tabColor: "1D4ED8", headers: ["externalNumber", "attendanceDate", "paycode_id"], rows: [], highlightCols: [0, 1, 2] },
      { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "code", "description"], rows: pcs.map(p => [p.id, p.code || "", p.description || ""]) }
    ]);
    btn.style.opacity = "1";
  };

  document.getElementById("tc-action-upload").onclick = () => {
    Notifications.clearLog("tc-log");
    AppState.cache.tc = null; AppState.cache.tcSuccessRows = []; AppState.cache.tcFailedRows = [];
    document.getElementById("tc-submit").disabled = true;
    document.getElementById("tc-dl-success").style.display = "none";
    document.getElementById("tc-dl-failed").style.display = "none";
    document.getElementById("tc-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    Router.go("screen-tc-upload");
  };

  wireFileInput("tc-file", "tc-file-name", "tc-submit", "tc");

  // ── GET: fetch one employee timecard (with retry) ───────
  async function tcFetchEmployee(extNum, date, debugMode) {
    const fullUrl = `${TC_GET_BASE()}?startDate=${date}&endDate=${date}&externalNumber=${encodeURIComponent(extNum)}&attributes=${encodeURIComponent(TC_ATTR)}`;

    if (debugMode) {
      Notifications.log("tc-log", `🔍 GET ${fullUrl}`, "info");
      Notifications.log("tc-log", `   startDate=${date}  endDate=${date}  externalNumber=${extNum}`, "info");
      Notifications.log("tc-log", `   Headers: Content-Type:application/json  X-Client-Type:Web  Accept:application/json`, "info");
    }

    let lastErr = "Unknown error";
    for (let attempt = 1; attempt <= TC_MAX_RETRIES; attempt++) {
      try {
        const r = await ApiTracker.fetch(fullUrl, { headers: apiH() }, "Timecard Update");
        if (r.status === 200) {
          let data;
          try { data = await r.json(); } catch (e) { return { ok: false, ext: extNum, date, url: fullUrl, status: r.status, body: `JSON parse error: ${e.message}` }; }
          if (!data || !data.length || !data[0].entries?.length) return { ok: false, ext: extNum, date, url: fullUrl, status: 200, body: `Empty entries in response` };
          const entries = data[0].entries;
          const entry = entries.find(e => String(e.employee?.externalNumber || "").trim() === String(extNum).trim())
                     || (entries.length === 1 ? entries[0] : null);
          if (!entry) return { ok: false, ext: extNum, date, url: fullUrl, status: 200, body: `No matching entry for externalNumber "${extNum}" in ${entries.length} entries` };
          return { ok: true, ext: extNum, date, empId: entry.employee.id, version: entry.attendancePaycode?.version ?? 0 };
        }
        const body = await r.text();
        lastErr = `Employee: ${extNum}\nDate: ${date}\nURL: ${fullUrl}\nHTTP Status: ${r.status}\nResponse Body: ${body}`;
        if (!tcTransient(r.status)) return { ok: false, ext: extNum, date, url: fullUrl, status: r.status, body };
      } catch (e) {
        lastErr = `Employee: ${extNum}\nDate: ${date}\nURL: ${fullUrl}\nHTTP Status: NETWORK_ERROR\nResponse Body: ${e.message}`;
      }
      if (attempt < TC_MAX_RETRIES) await tcSleep(TC_BACKOFF_MS * attempt);
    }
    return { ok: false, ext: extNum, date, url: fullUrl, status: "TIMEOUT", body: lastErr };
  }

  // ── POST: batch for one date (with retry) ───────────────
  async function tcPostBatch(date, entries, debugMode) {
    const url = TC_POST_BASE();
    const payload = { attendanceDate: date, entries };
    if (debugMode) {
      Notifications.log("tc-log", `🔍 POST URL: ${url}`, "info");
      Notifications.log("tc-log", `   POST Payload: ${JSON.stringify(payload)}`, "info");
    }
    let lastBody = "", lastStatus = "";
    for (let attempt = 1; attempt <= TC_MAX_RETRIES; attempt++) {
      try {
        const r = await ApiTracker.fetch(url, { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Timecard Update");
        const body = await r.text();
        lastStatus = r.status; lastBody = body;
        if (debugMode) Notifications.log("tc-log", `   POST Response (HTTP ${r.status}): ${body.substring(0, 300)}`, "info");
        if (r.status === 200 || r.status === 201) return { ok: true, status: r.status, body };
        if (!tcTransient(r.status)) return { ok: false, status: r.status, body };
      } catch (e) { lastBody = e.message; lastStatus = "NETWORK_ERROR"; }
      if (attempt < TC_MAX_RETRIES) await tcSleep(TC_BACKOFF_MS * attempt);
    }
    return { ok: false, status: lastStatus || "RETRIES_EXHAUSTED", body: lastBody };
  }

  // ── Verification GET ─────────────────────────────────────
  async function tcVerifyUpdate(extNum, date, expectedPcId, debugMode) {
    const fullUrl = `${TC_GET_BASE()}?startDate=${date}&endDate=${date}&externalNumber=${encodeURIComponent(extNum)}&attributes=${encodeURIComponent(TC_ATTR)}`;
    if (debugMode) Notifications.log("tc-log", `   🔍 Verification GET: ${fullUrl}`, "info");
    try {
      const r = await ApiTracker.fetch(fullUrl, { headers: apiH() }, "Timecard Update");
      if (r.status !== 200) {
        const body = await r.text();
        if (debugMode) Notifications.log("tc-log", `   Verification GET Response (HTTP ${r.status}): ${body.substring(0, 300)}`, "info");
        return { verified: false, reason: `Verification GET returned HTTP ${r.status}: ${body.substring(0, 150)}` };
      }
      let data;
      try { data = await r.json(); } catch (e) { return { verified: false, reason: `Verification GET JSON parse error: ${e.message}` }; }
      if (debugMode) Notifications.log("tc-log", `   Verification GET Response: ${JSON.stringify(data).substring(0, 400)}`, "info");
      if (!data || !data.length || !data[0].entries?.length) return { verified: false, reason: `Verification GET returned empty entries` };
      const entries = data[0].entries;
      const entry = entries.find(e => String(e.employee?.externalNumber || "").trim() === String(extNum).trim())
                 || (entries.length === 1 ? entries[0] : null);
      if (!entry) return { verified: false, reason: `Verification GET: no matching entry for externalNumber "${extNum}"` };
      const actualPcId = entry.attendancePaycode?.paycode?.id;
      if (String(actualPcId) === String(expectedPcId)) return { verified: true, actualPcId };
      return { verified: false, reason: `POST returned HTTP 200 but attendance paycode was not updated. Expected paycode.id=${expectedPcId}, got ${actualPcId}` };
    } catch (e) {
      return { verified: false, reason: `Verification GET network error: ${e.message}` };
    }
  }

  document.getElementById("tc-dl-success").onclick = () => {
    downloadExcel("tc_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["externalNumber", "attendanceDate", "paycode_id", "employee_id", "version"],
      rows: (AppState.cache.tcSuccessRows || []).map(r => [r.ext, r.date, r.pcId, r.empId, r.version])
    }]);
  };
  document.getElementById("tc-dl-failed").onclick = () => {
    downloadExcel("tc_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["externalNumber", "attendanceDate", "paycode_id", "url", "status", "response_body"],
      rows: (AppState.cache.tcFailedRows || []).map(r => [r.ext, r.date, r.pcId || "", r.url || "", String(r.status || ""), r.body || ""])
    }]);
  };

  // ── Submit ────────────────────────────────────────────────
  document.getElementById("tc-submit").onclick = async () => {
    const btn = document.getElementById("tc-submit");
    const rows = AppState.cache.tc || [];
    const debug = document.getElementById("tc-debug").checked;
    Notifications.clearLog("tc-log");
    document.getElementById("tc-dl-success").style.display = "none";
    document.getElementById("tc-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("tc-status", "❌ No data found in file"); return; }

    function col(row, name) {
      const k = Object.keys(row).find(k => k.trim().toLowerCase() === name.toLowerCase());
      return k ? String(row[k] || "").trim() : "";
    }

    const sample = rows[0];
    if (!Object.keys(sample).some(k => k.trim().toLowerCase() === "externalnumber") ||
        !Object.keys(sample).some(k => k.trim().toLowerCase() === "attendancedate") ||
        !Object.keys(sample).some(k => k.trim().toLowerCase() === "paycode_id")) {
      Notifications.error("tc-status", "❌ Missing required columns — need: externalNumber, attendanceDate, paycode_id");
      return;
    }

    const parseErrors = [], validRows = [];
    rows.forEach((row, i) => {
      const ext = col(row, "externalNumber");
      const rawDate = col(row, "attendanceDate");
      const date = tcNormalizeDate(rawDate);
      const pcId = parseIntSafe(col(row, "paycode_id"));
      if (!ext || !date || pcId === null) parseErrors.push(`Row ${i + 2}: ext="${ext}" date="${rawDate}" paycode="${col(row, "paycode_id")}"`);
      else validRows.push({ ext, date, rawDate, pcId });
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("tc-log", `⚠️ Skipped — ${e}`, "fail"); Audit.onValidationError(e); });

    const byDate = {};
    validRows.forEach(r => { if (!byDate[r.date]) byDate[r.date] = []; byDate[r.date].push(r); });
    const dateGroups = Object.entries(byDate);
    if (!dateGroups.length) { Notifications.error("tc-status", "❌ No valid rows found"); return; }

    Notifications.loading(btn, `Processing 0/${dateGroups.length} date(s)...`);
    Notifications.progress.show("tc-prog");
    AppState.cache.tcSuccessRows = []; AppState.cache.tcFailedRows = [];
    let totalSuccess = 0, totalFailed = 0, datesProcessed = 0;

    for (const [date, dateRows] of dateGroups) {
      Notifications.loading(btn, `Date ${datesProcessed + 1}/${dateGroups.length}: GET ${dateRows.length} employee(s) concurrently...`);

      const fetchResults = await Promise.allSettled(dateRows.map(row => tcFetchEmployee(row.ext, date, debug)));

      const entries = [];
      const entryMeta = [];
      fetchResults.forEach((result, idx) => {
        const row = dateRows[idx];
        if (result.status === "rejected" || !result.value?.ok) {
          const r = result.value || {};
          Notifications.log("tc-log", `❌ GET failed — ext: ${row.ext} | date: ${date}`, "fail");
          if (r.url) Notifications.log("tc-log", `   URL: ${r.url}`, "fail");
          if (r.status) Notifications.log("tc-log", `   HTTP Status: ${r.status}`, "fail");
          if (r.body) Notifications.log("tc-log", `   Response Body: ${String(r.body).substring(0, 300)}`, "fail");
          AppState.cache.tcFailedRows.push({ ext: row.ext, date, pcId: row.pcId, url: r.url || "", status: r.status || "", body: parseApiError(String(r.body || "")) });
          totalFailed++;
        } else {
          const { empId, version } = result.value;
          entries.push({
            index: entries.length + 1,
            employee: { id: empId },
            attendancePaycode: { attendanceDate: date, employee: { id: empId }, paycode: { id: row.pcId }, version }
          });
          entryMeta.push({ ext: row.ext, pcId: row.pcId, empId, version });
        }
      });

      if (!entries.length) {
        datesProcessed++;
        Notifications.progress.set("tc-bar", (datesProcessed / dateGroups.length) * 100);
        continue;
      }

      Notifications.loading(btn, `Date ${datesProcessed + 1}/${dateGroups.length}: posting batch (${entries.length} entries)...`);
      const batchResult = await tcPostBatch(date, entries, debug);

      if (batchResult.ok) {
        Notifications.loading(btn, `Date ${datesProcessed + 1}/${dateGroups.length}: verifying ${entryMeta.length} update(s)...`);
        const verifyResults = await Promise.allSettled(entryMeta.map(m => tcVerifyUpdate(m.ext, date, m.pcId, debug).then(v => ({ ...v, meta: m }))));
        verifyResults.forEach(result => {
          const v = result.status === "fulfilled" ? result.value : { verified: false, reason: result.reason?.message, meta: {} };
          const m = v.meta || {};
          if (v.verified) {
            Notifications.log("tc-log", `✅ Verified — ext: ${m.ext} | date: ${date} | paycode: ${m.pcId}`, "ok");
            AppState.cache.tcSuccessRows.push({ ext: m.ext, date, pcId: m.pcId, empId: m.empId, version: m.version });
            totalSuccess++;
          } else {
            Notifications.log("tc-log", `❌ Verification failed — ext: ${m.ext} | date: ${date}`, "fail");
            Notifications.log("tc-log", `   ${v.reason || "Unknown verification error"}`, "fail");
            AppState.cache.tcFailedRows.push({ ext: m.ext, date, pcId: m.pcId, url: TC_POST_BASE(), status: "VERIFY_FAILED", body: v.reason || "" });
            totalFailed++;
          }
        });
      } else {
        Notifications.log("tc-log", `⚠️ Date ${date}: batch failed (${batchResult.status}) — retrying individually...`, "info");
        if (batchResult.body) Notifications.log("tc-log", `⚠️ ${parseApiError(String(batchResult.body))}`, "info");

        const individualResults = await Promise.allSettled(
          entryMeta.map((m, idx) => tcPostBatch(date, [{ ...entries[idx], index: 1 }], debug).then(r => ({ ...r, meta: m })))
        );

        const verifyTasks = [];
        individualResults.forEach(result => {
          const r = result.status === "fulfilled" ? result.value : { ok: false, body: result.reason?.message };
          const m = r.meta || {};
          if (r.ok) {
            verifyTasks.push({ m, promise: tcVerifyUpdate(m.ext, date, m.pcId, debug).then(v => ({ ...v, meta: m })) });
          } else {
            Notifications.log("tc-log", `  ❌ POST failed — ext: ${m.ext} | date: ${date} | HTTP ${r.status || "?"}`, "fail");
            if (r.body) Notifications.log("tc-log", `     ${parseApiError(String(r.body))}`, "fail");
            AppState.cache.tcFailedRows.push({ ext: m.ext, date, pcId: m.pcId, url: TC_POST_BASE(), status: r.status || "", body: parseApiError(String(r.body || "")) });
            totalFailed++;
          }
        });

        if (verifyTasks.length) {
          Notifications.loading(btn, `Date ${datesProcessed + 1}/${dateGroups.length}: verifying ${verifyTasks.length} individual update(s)...`);
          const verifyResults = await Promise.allSettled(verifyTasks.map(t => t.promise));
          verifyResults.forEach(result => {
            const v = result.status === "fulfilled" ? result.value : { verified: false, reason: result.reason?.message, meta: {} };
            const m = v.meta || {};
            if (v.verified) {
              Notifications.log("tc-log", `  ✅ Verified — ext: ${m.ext} | date: ${date} | paycode: ${m.pcId}`, "ok");
              AppState.cache.tcSuccessRows.push({ ext: m.ext, date, pcId: m.pcId, empId: m.empId, version: m.version });
              totalSuccess++;
            } else {
              Notifications.log("tc-log", `  ❌ Verification failed — ext: ${m.ext} | date: ${date}`, "fail");
              Notifications.log("tc-log", `     ${v.reason || "Unknown verification error"}`, "fail");
              AppState.cache.tcFailedRows.push({ ext: m.ext, date, pcId: m.pcId, url: TC_POST_BASE(), status: "VERIFY_FAILED", body: v.reason || "" });
              totalFailed++;
            }
          });
        }
      }

      datesProcessed++;
      Notifications.progress.set("tc-bar", (datesProcessed / dateGroups.length) * 100);
    }

    Audit.onDbOp("updated", totalSuccess);
    Notifications.log("tc-log", `━━━━━━━━━━━━━━━━━━`, "info");
    Notifications.log("tc-log", `✅ Updated: ${totalSuccess}  ❌ Failed: ${totalFailed}  (${parseErrors.length} skipped at parse)`, totalFailed === 0 ? "ok" : "info");
    Notifications.status("tc-status", `Done — ${totalSuccess} updated, ${totalFailed} failed${parseErrors.length ? `, ${parseErrors.length} skipped` : ""}`, totalFailed === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Fetch & Update Timecards");
    Notifications.progress.hide("tc-prog");
    if (AppState.cache.tcSuccessRows.length) document.getElementById("tc-dl-success").style.display = "block";
    if (AppState.cache.tcFailedRows.length) document.getElementById("tc-dl-failed").style.display = "block";
  };

  console.log("✅ Timecard Update module loaded — POST /api/attendance/timecards, verification GET after every update");
}
