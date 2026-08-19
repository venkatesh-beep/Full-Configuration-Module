/* =========================================================
 * ot-approval.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/ot-approval.js — BeeForce Configuration Portal
// Owns: screen-ota, screen-ota-upload
// POST /api/attendance/overtime_requests/action   {action:"ADD", data:[...]}
// Exports: init(context)
// =========================================================

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, resolveEmployeeId, modal } = ctx;

  const OTA_POST_URL = () => `${AppState.BASE_URL}/api/attendance/overtime_requests/action`;
  const OTA_BATCH = 28;

  if (!document.getElementById("screen-ota")) {
    const main = document.createElement("div");
    main.id = "screen-ota"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">⏱️ OT Approval</span></div>
      <div class="bf-module-header"><div class="mh-icon">⏱️</div><div><div class="mh-title">OT / Post Approval</div><div class="mh-sub">Select ID type · Download Template · Upload & Submit</div></div></div>

      <div class="bf-section-label" style="margin-top:4px">Step 1 — Choose upload type</div>
      <div class="pun-dir-toggle" id="ota-id-toggle">
        <button class="pun-dir-btn active" data-idtype="ext">📋 By External Number</button>
        <button class="pun-dir-btn" data-idtype="emp">🔢 By Employee ID</button>
      </div>
      <div id="ota-main-hint" style="font-size:12px;color:#6B7280;margin-bottom:14px;padding:8px 12px;background:#F9FAFB;border-radius:8px;border:1px solid #E5E7EB;">
        Template columns: <b>externalNumber</b> · attendanceDate · duration (HH:MM)
      </div>

      <div class="bf-section-label">Step 2 — Download template or upload filled file</div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="ota-action-tpl">
          <div class="ac-icon">⬇️</div>
          <div class="ac-name">Download Template</div>
          <div class="ac-desc">Downloads the correct template based on your selection above</div>
        </div>
        <div class="bf-action-card" id="ota-action-upload">
          <div class="ac-icon">📤</div>
          <div class="ac-name">Upload & Submit</div>
          <div class="ac-desc">Upload filled template · batch POST to OT action API</div>
        </div>
      </div>`;
    modal.appendChild(main);

    const upload = document.createElement("div");
    upload.id = "screen-ota-upload"; upload.style.display = "none";
    upload.innerHTML = `
      <div class="bf-breadcrumb">
        <span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span>
        <span class="bc-link" data-go="screen-ota">⏱️ OT Approval</span><span class="bc-sep">›</span>
        <span class="bc-cur">Upload & Submit</span>
      </div>
      <div id="ota-upload-idtype-label" class="bf-info-box" style="margin-bottom:12px">
        Mode: <b id="ota-upload-mode-label">By External Number</b> —
        <span id="ota-upload-mode-hint">Employee IDs resolved via externalNumber before posting</span>.<br>
        Change mode on the previous screen. ← <span class="bc-link" style="cursor:pointer" data-go="screen-ota">Go back</span>
      </div>
      <div id="ota-status" class="bf-status"></div>
      <label class="bf-file-label" for="ota-file"><span id="ota-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="ota-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="ota-prog"><div class="bf-pb" id="ota-bar" style="width:0%"></div></div>
      <div class="bf-log" id="ota-log"></div>
      <button class="bf-btn bf-success" id="ota-submit" disabled>🚀 Submit OT Requests</button>
      <button class="bf-btn bf-outline" id="ota-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="ota-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(upload);

    Router.register("screen-ota", "screen-ota-upload");
    [main, upload].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });

    // Toggle wiring (only once, at injection time)
    const toggle = document.getElementById("ota-id-toggle");
    const hint = document.getElementById("ota-main-hint");
    toggle.querySelectorAll(".pun-dir-btn").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        toggle.querySelectorAll(".pun-dir-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const byEmp = btn.dataset.idtype === "emp";
        if (hint) hint.innerHTML = byEmp
          ? "Template columns: <b>employeeID</b> &middot; attendanceDate &middot; duration (HH:MM)"
          : "Template columns: <b>externalNumber</b> &middot; attendanceDate &middot; duration (HH:MM)";
      });
    });
  }

  function otaDownloadTemplate() {
    const byEmp = document.querySelector("#ota-id-toggle .pun-dir-btn.active")?.dataset.idtype === "emp";
    if (byEmp) {
      downloadExcel("ot_by_employee_id_template.xlsx", [{ name: "OT_ByEmployeeID", tabColor: "7C3AED", headers: ["employeeID", "attendanceDate", "duration"], rows: [], highlightCols: [0, 1, 2] }]);
    } else {
      downloadExcel("ot_by_external_number_template.xlsx", [{ name: "OT_ByExternalNumber", tabColor: "D97706", headers: ["externalNumber", "attendanceDate", "duration"], rows: [], highlightCols: [0, 1, 2] }]);
    }
  }
  document.getElementById("ota-action-tpl").onclick = () => otaDownloadTemplate();

  document.getElementById("ota-action-upload").onclick = () => {
    Notifications.clearLog("ota-log");
    AppState.cache.ota = null; AppState.cache.otaSuccessRows = []; AppState.cache.otaFailedRows = [];
    document.getElementById("ota-submit").disabled = true;
    document.getElementById("ota-dl-success").style.display = "none";
    document.getElementById("ota-dl-failed").style.display = "none";
    document.getElementById("ota-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    const byEmp = document.querySelector("#ota-id-toggle .pun-dir-btn.active")?.dataset.idtype === "emp";
    const lbl = document.getElementById("ota-upload-mode-label");
    const hint = document.getElementById("ota-upload-mode-hint");
    if (lbl) lbl.textContent = byEmp ? "By Employee ID" : "By External Number";
    if (hint) hint.textContent = byEmp ? "Employee IDs used directly — no lookup needed" : "Employee IDs resolved from externalNumber before posting";
    Router.go("screen-ota-upload");
  };

  wireFileInput("ota-file", "ota-file-name", "ota-submit", "ota");

  document.getElementById("ota-dl-success").onclick = () => {
    downloadExcel("ot_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["externalNumber", "attendanceDate", "duration", "employee_id"],
      rows: (AppState.cache.otaSuccessRows || []).map(r => [r.ext, r.date, r.duration, r.empId])
    }]);
  };
  document.getElementById("ota-dl-failed").onclick = () => {
    downloadExcel("ot_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["externalNumber", "attendanceDate", "duration", "error", "status", "response_body"],
      rows: (AppState.cache.otaFailedRows || []).map(r => [r.ext, r.date, r.duration, r.error || "", String(r.status || ""), r.body || ""])
    }]);
  };

  document.getElementById("ota-submit").onclick = async () => {
    const btn = document.getElementById("ota-submit");
    const rows = AppState.cache.ota || [];
    Notifications.clearLog("ota-log");
    document.getElementById("ota-dl-success").style.display = "none";
    document.getElementById("ota-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("ota-status", "❌ No data found in file"); return; }

    function col(row, name) {
      const k = Object.keys(row).find(k => k.trim().toLowerCase() === name.toLowerCase());
      return k ? String(row[k] || "").trim() : "";
    }

    const byEmp = document.querySelector("#ota-id-toggle .pun-dir-btn.active")?.dataset.idtype === "emp";

    const colKeys = Object.keys(rows[0]).map(k => k.trim().toLowerCase());
    if (byEmp && (!colKeys.includes("employeeid") || !colKeys.includes("attendancedate") || !colKeys.includes("duration"))) {
      Notifications.error("ota-status", "❌ Missing columns — need: employeeID, attendanceDate, duration"); return;
    }
    if (!byEmp && (!colKeys.includes("externalnumber") || !colKeys.includes("attendancedate") || !colKeys.includes("duration"))) {
      Notifications.error("ota-status", "❌ Missing columns — need: externalNumber, attendanceDate, duration"); return;
    }

    const parseErrors = [], validRows = [];
    rows.forEach((row, i) => {
      const id = byEmp ? col(row, "employeeID") : col(row, "externalNumber");
      const date = col(row, "attendanceDate");
      const duration = col(row, "duration");
      if (!id || !date || !duration) { parseErrors.push(`Row ${i + 2}: missing required field`); return; }
      validRows.push({ id, date, duration });
    });
    if (parseErrors.length) parseErrors.forEach(e => { Notifications.log("ota-log", `⚠️ ${e}`, "fail"); Audit.onValidationError(e); });
    if (!validRows.length) { Notifications.error("ota-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, `${byEmp ? "Using" : "Resolving"} ${validRows.length} employee ID(s)...`);
    Notifications.progress.show("ota-prog");
    AppState.cache.otaSuccessRows = []; AppState.cache.otaFailedRows = [];
    let totalSuccess = 0, totalFailed = 0;

    let resolved = [];
    if (byEmp) {
      validRows.forEach(row => {
        const empId = parseIntSafe(row.id);
        if (empId !== null) resolved.push({ ...row, empId, ext: row.id });
        else {
          Notifications.log("ota-log", `❌ Invalid employee ID: "${row.id}"  date: ${row.date}`, "fail");
          AppState.cache.otaFailedRows.push({ ext: row.id, date: row.date, duration: row.duration, error: `Invalid employee ID: "${row.id}"` });
          totalFailed++;
        }
      });
    } else {
      const resolveResults = await Promise.allSettled(
        validRows.map(row => resolveEmployeeId(row.id).then(empId => ({ ...row, empId, ext: row.id })).catch(e => ({ ...row, ext: row.id, _err: e.message })))
      );
      resolveResults.forEach(r => {
        const v = r.status === "fulfilled" ? r.value : { ...r.reason, _err: r.reason?.message || "Unknown" };
        if (!v._err) resolved.push(v);
        else {
          Notifications.log("ota-log", `❌ Lookup failed — ext: ${v.ext} | ${v._err}`, "fail");
          AppState.cache.otaFailedRows.push({ ext: v.ext, date: v.date, duration: v.duration, error: v._err });
          totalFailed++;
        }
      });
    }
    Notifications.progress.set("ota-bar", 30);

    if (!resolved.length) {
      Notifications.error("ota-status", "❌ No employees resolved");
      Notifications.doneLoading(btn, "🚀 Submit OT Requests");
      Notifications.progress.hide("ota-prog");
      if (AppState.cache.otaFailedRows.length) document.getElementById("ota-dl-failed").style.display = "block";
      return;
    }

    const byDate = {};
    resolved.forEach(row => { if (!byDate[row.date]) byDate[row.date] = []; byDate[row.date].push(row); });
    const dateGroups = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b));
    const totalBatches = dateGroups.reduce((sum, [, rows]) => sum + Math.ceil(rows.length / OTA_BATCH), 0);
    let batchesDone = 0;

    for (const [date, dateRows] of dateGroups) {
      for (let start = 0; start < dateRows.length; start += OTA_BATCH) {
        const chunk = dateRows.slice(start, start + OTA_BATCH);
        batchesDone++;
        Notifications.loading(btn, `${date} · Batch ${batchesDone}/${totalBatches} (${chunk.length} records)...`);

        const data = chunk.map((row, idx) => ({ id: start + idx, attendanceDate: date, requestDuration: row.duration, employee: { id: row.empId } }));

        try {
          const r = await ApiTracker.fetch(OTA_POST_URL(), { method: "POST", headers: apiH(), body: JSON.stringify({ action: "ADD", data }) }, "OT Approval");
          const body = await r.text();

          if (r.status === 200 || r.status === 201) {
            chunk.forEach(row => { AppState.cache.otaSuccessRows.push({ ext: row.ext, date: row.date, duration: row.duration, empId: row.empId }); totalSuccess++; });
          } else {
            Notifications.log("ota-log", `⚠️ ${date} batch ${batchesDone} failed (HTTP ${r.status}) — retrying individually...`, "info");
            Notifications.log("ota-log", `⚠️ ${parseApiError(body)}`, "info");
            for (const row of chunk) {
              try {
                const r2 = await ApiTracker.fetch(OTA_POST_URL(), {
                  method: "POST", headers: apiH(),
                  body: JSON.stringify({ action: "ADD", data: [{ id: 0, attendanceDate: date, requestDuration: row.duration, employee: { id: row.empId } }] })
                }, "OT Approval");
                const body2 = await r2.text();
                if (r2.status === 200 || r2.status === 201) {
                  AppState.cache.otaSuccessRows.push({ ext: row.ext, date: row.date, duration: row.duration, empId: row.empId });
                  totalSuccess++;
                } else {
                  Notifications.log("ota-log", `  ❌ empId:${row.empId} | ${parseApiError(body2)}`, "fail");
                  AppState.cache.otaFailedRows.push({ ext: row.ext, date: row.date, duration: row.duration, error: parseApiError(body2) });
                  totalFailed++;
                }
              } catch (e2) {
                Notifications.log("ota-log", `  ❌ empId:${row.empId} | ${e2.message}`, "fail");
                AppState.cache.otaFailedRows.push({ ext: row.ext, date: row.date, duration: row.duration, error: e2.message });
                totalFailed++;
              }
            }
          }
        } catch (e) {
          Notifications.log("ota-log", `❌ Batch ${batchesDone} network error — ${e.message}`, "fail");
          chunk.forEach(row => { AppState.cache.otaFailedRows.push({ ext: row.ext, date: row.date, duration: row.duration, error: e.message }); totalFailed++; });
        }

        Notifications.progress.set("ota-bar", 30 + (batchesDone / totalBatches) * 70);
      }
    }

    Audit.onDbOp("created", totalSuccess);
    Notifications.log("ota-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("ota-log", `✅ Submitted: ${totalSuccess}  ❌ Failed: ${totalFailed}${parseErrors.length ? `  ⚠️ Skipped: ${parseErrors.length}` : ""}`, totalFailed === 0 ? "ok" : "info");
    Notifications.status("ota-status", `Done — ${totalSuccess} submitted, ${totalFailed} failed${parseErrors.length ? `, ${parseErrors.length} skipped` : ""}`, totalFailed === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Submit OT Requests");
    Notifications.progress.hide("ota-prog");
    if (AppState.cache.otaSuccessRows.length) document.getElementById("ota-dl-success").style.display = "block";
    if (AppState.cache.otaFailedRows.length) document.getElementById("ota-dl-failed").style.display = "block";
  };
}
