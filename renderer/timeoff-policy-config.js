/* =========================================================
 * timeoff-policy-config.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-topolcfg, screen-topolcfg-create, screen-topolcfg-view,
 *       screen-topolcfg-delete
 * GET    /api/attendance/time_off_policies/?projection=FULL
 * POST   /api/attendance/time_off_policies/          (create, WITH trailing slash)
 * PUT    /api/attendance/time_off_policies/{id}      (update, NO trailing slash)
 * DELETE /api/attendance/time_off_policies/{id}      (NO trailing slash)
 *
 * HEADER LAYOUT — 44 columns, matches your exact spreadsheet exactly.
 * Because several header names REPEAT (Applicable ×4, Period ×2,
 * Reference Date ×2, Min Days ×2, Max Days ×2), this module reads the
 * uploaded file as position-indexed arrays (header:1 mode) instead of
 * {columnName: value} objects — object keys can't hold duplicates, so
 * reading it the normal way would silently lose data for every repeated
 * column except the last one. This module does its OWN file reading;
 * it does not use the shared wireFileInput() helper.
 *
 * Each row = ONE approval level for that policy (policy 15 with 2
 * approvalConfigs → 2 rows). All policy-level fields repeat identically
 * on every row. "Paycodes" and "Skip Paycodes" are single comma-separated
 * lists, repeated the same way on every row for that policy.
 *
 * All reference dates are plain ISO YYYY-MM-DD, both on screen and in
 * the payload — no format conversion at all.
 *
 * approverType is ALWAYS forced to "ATTRIBUTE" in the payload,
 * regardless of what's in the "Approver Type" column.
 * probationaryPeriod / probationaryPeriodValue are OPTIONAL — omitted
 * from the payload entirely unless actually filled in (the API rejects
 * a blank enum / a 0 value for policies that don't use probation).
 * ========================================================= */

var TOPOL_HEADERS = [
  "id", "Name", "Description", "Paycode ID", "Paycode Group", "Past Signed Off Periods",
  "Probationary Period", "Probationary Period Value",
  "Approval Level", "Approver Type", "Remarks", "Notes", "Consider Sign Off", "Remarks Required",
  "Ignore Schedule Paycodes", "Enable For Employee", "Approver/s", "TAT Duration", "TAT Action",
  "Reminder Notification Duration/s", "Send Notification", "Send Employee Notification",
  "Send Push Notification", "Enable Workflow No Emails", "Enable TAT For Cancellation",
  "Applicable", "Count", "Period", "Reference Date",
  "Applicable", "Min Days", "Max Days", "Apply In Block",
  "Applicable", "Min Days", "Max Days", "Period", "Reference Date", "Ignore Sandwich Rule",
  "Applicable", "Before Days *", "After Days *",
  "Paycodes", "Skip Paycodes"
];

// Column positions (0-based) — used instead of name lookup because
// several names above repeat and can't be told apart by text alone.
var C = {
  ID: 0, NAME: 1, DESC: 2, PAYCODE_ID: 3, PAYCODE_GROUP: 4, PAST_SIGNED: 5,
  PROB_PERIOD: 6, PROB_VALUE: 7,
  APPROVAL_LEVEL: 8, APPROVER_TYPE: 9, REMARKS: 10, NOTES: 11, CONSIDER_SIGNOFF: 12, REMARKS_REQUIRED: 13,
  IGNORE_SCHEDULE_PAYCODES: 14, ENABLE_FOR_EMPLOYEE: 15, APPROVER: 16, TAT_DURATION: 17, TAT_ACTION: 18,
  REMINDER_DURATIONS: 19, SEND_NOTIFICATION: 20, SEND_EMP_NOTIFICATION: 21, PUSH_NOTIFICATION: 22,
  ENABLE_WORKFLOW_NO_EMAILS: 23, ENABLE_TAT_CANCEL: 24,
  UL_APPLICABLE: 25, UL_COUNT: 26, UL_PERIOD: 27, UL_REFDATE: 28,
  AV_APPLICABLE: 29, AV_MIN: 30, AV_MAX: 31, AV_BLOCK: 32,
  DU_APPLICABLE: 33, DU_MIN: 34, DU_MAX: 35, DU_PERIOD: 36, DU_REFDATE: 37, DU_IGNORE_SANDWICH: 38,
  SR_APPLICABLE: 39, SR_BEFORE: 40, SR_AFTER: 41,
  PAYCODES: 42, SKIP_PAYCODES: 43
};
var TOPOL_INPUT_COLS = [1, 2, 3]; // Name, Description, Paycode ID

// Per-column header cell colors (replaces merged group banners — more
// robust since it needs no cell-merge rendering support from whatever
// app opens the file). One entry per column, in TOPOL_HEADERS order.
var TOPOL_GROUP_COLOR_DEFS = [
  { label: "Basic Information", span: 16, bg: "E5E7EB", font: "111827" },   // light gray
  { label: "Approval Configuration", span: 9, bg: "16A34A", font: "FFFFFF" }, // green
  { label: "Usage Limit", span: 4, bg: "2563EB", font: "FFFFFF" },           // blue
  { label: "Availing Limit", span: 4, bg: "D97706", font: "FFFFFF" },        // amber
  { label: "Document Upload", span: 6, bg: "7C3AED", font: "FFFFFF" },       // purple
  { label: "Sandwich Rule", span: 5, bg: "DB2777", font: "FFFFFF" }          // pink
];
var TOPOL_HEADER_COLORS = (function () {
  var arr = [];
  TOPOL_GROUP_COLOR_DEFS.forEach(function (g) {
    for (var i = 0; i < g.span; i++) arr.push({ bg: g.bg, font: g.font });
  });
  return arr;
})();

var TOPOL_DROPDOWNS_HEADERS = [
  "Consider Sign Off", "Ignore Schedule Paycodes", "Enable For Employee", "Probationary Period", "Remarks Required",
  "Applicable (Usage Limit)", "Period (Usage Limit)", "Applicable (Availing Limit)", "Apply In Block",
  "Applicable (Document Upload)", "Ignore Sandwich Rule", "Period (Document Upload)", "Applicable (Sandwich Rule)",
  "Send Notification", "Send Employee Notification", "Send Push Notification",
  "Enable Workflow No Emails", "Enable TAT For Cancellation", "TAT Action"
];
var TOPOL_DROPDOWNS_ROWS = [
  ["TRUE", "TRUE", "TRUE", "Days", "TRUE", "TRUE", "Weekly", "TRUE", "TRUE", "TRUE", "TRUE", "Weekly", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "TRUE", "APPROVE"],
  ["FALSE", "FALSE", "FALSE", "Weeks", "FALSE", "FALSE", "Monthly", "FALSE", "FALSE", "FALSE", "FALSE", "Monthly", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "REJECT"],
  ["", "", "", "Months", "", "", "Quaterly", "", "", "", "", "Quaterly", "", "", "", "", "", "", ""],
  ["", "", "", "Years", "", "", "Yearly", "", "", "", "", "Yearly", "", "", "", "", "", "", ""]
];

function topolBoolStr(v) { return v ? "TRUE" : "FALSE"; }
function topolVal(v) { return (v === null || v === undefined) ? "" : v; }
function topolToBool(v) { return ["true", "1", "yes"].indexOf(String(v || "").toLowerCase().trim()) !== -1; }

/** Flattens ONE policy (FULL projection) into one row per approval
 *  level. Paycodes/Skip Paycodes are comma-joined lists, repeated
 *  identically on every row. All dates stay plain ISO (YYYY-MM-DD). */
function topolFlattenPolicy(p) {
  var ul = (p.usageLimits && p.usageLimits[0]) || {};
  var av = p.availingLimit || {};
  var du = p.documentUpload || {};
  var sr = p.sandwichRule || {};
  var configs = (p.approvalConfigs && p.approvalConfigs.length) ? p.approvalConfigs : [{}];
  var spList = (p.sandwichPaycodes || []).map(function (x) { return x.id; }).join(",");
  var sspList = (p.sandwichSkipPaycodes || []).map(function (x) { return x.id; }).join(",");

  var rows = [];
  configs.forEach(function (ac) {
    var row = [];
    row[C.ID] = p.id; row[C.NAME] = p.name || ""; row[C.DESC] = p.description || "";
    row[C.PAYCODE_ID] = (p.paycode && p.paycode.id) || ""; row[C.PAYCODE_GROUP] = p.paycodeGroup || "";
    row[C.PAST_SIGNED] = topolVal(p.numOfPastSignedOfPeriods);
    row[C.PROB_PERIOD] = p.probationaryPeriod || ""; row[C.PROB_VALUE] = topolVal(p.probationaryPeriodValue);
    row[C.APPROVAL_LEVEL] = topolVal(ac.level); row[C.APPROVER_TYPE] = ac.approverType || "";
    row[C.REMARKS] = p.remarks || ""; row[C.NOTES] = p.notes || "";
    row[C.CONSIDER_SIGNOFF] = topolBoolStr(p.considerSignOff); row[C.REMARKS_REQUIRED] = topolBoolStr(p.remarksRequired);
    row[C.IGNORE_SCHEDULE_PAYCODES] = topolBoolStr(p.ignoreSchedulePaycodes); row[C.ENABLE_FOR_EMPLOYEE] = topolBoolStr(p.enableForEmployee);
    row[C.APPROVER] = ac.approver || ""; row[C.TAT_DURATION] = ac.tatDuration || ""; row[C.TAT_ACTION] = ac.tatAction || "";
    row[C.REMINDER_DURATIONS] = ac.reminderNotificationDurations || "";
    row[C.SEND_NOTIFICATION] = topolBoolStr(ac.sendNotification); row[C.SEND_EMP_NOTIFICATION] = topolBoolStr(ac.sendEmployeeNotification);
    row[C.PUSH_NOTIFICATION] = topolBoolStr(ac.pushNotification); row[C.ENABLE_WORKFLOW_NO_EMAILS] = topolBoolStr(ac.enableWorkflowNoEmails);
    row[C.ENABLE_TAT_CANCEL] = topolBoolStr(ac.enableTatForCancellation);
    row[C.UL_APPLICABLE] = topolBoolStr(ul.applicable); row[C.UL_COUNT] = topolVal(ul.count); row[C.UL_PERIOD] = ul.period || ""; row[C.UL_REFDATE] = ul.referenceDate || "";
    row[C.AV_APPLICABLE] = topolBoolStr(av.applicable); row[C.AV_MIN] = topolVal(av.minDays); row[C.AV_MAX] = topolVal(av.maxDays); row[C.AV_BLOCK] = topolBoolStr(av.applyInBlock);
    row[C.DU_APPLICABLE] = topolBoolStr(du.applicable); row[C.DU_MIN] = topolVal(du.minDays); row[C.DU_MAX] = topolVal(du.maxDays);
    row[C.DU_PERIOD] = du.period || ""; row[C.DU_REFDATE] = du.referenceDate || ""; row[C.DU_IGNORE_SANDWICH] = topolBoolStr(du.ignoreSandwichRule);
    row[C.SR_APPLICABLE] = topolBoolStr(sr.applicable); row[C.SR_BEFORE] = topolVal(sr.beforeDays); row[C.SR_AFTER] = topolVal(sr.afterDays);
    row[C.PAYCODES] = spList; row[C.SKIP_PAYCODES] = sspList;
    rows.push(row);
  });
  return rows;
}

function init(ctx) {
  var AppState = ctx.AppState;
  var apiH = ctx.apiH;
  var downloadExcel = ctx.downloadExcel;
  var parseApiError = ctx.parseApiError;
  var parseIntSafe = ctx.parseIntSafe;
  var fetchPaycodesRef = ctx.fetchPaycodesRef;
  var Notifications = ctx.Notifications;
  var Router = ctx.Router;
  var Audit = ctx.Audit;
  var ApiTracker = ctx.ApiTracker;
  var modal = ctx.modal;

  var TOPOL_BASE = function () { return AppState.BASE_URL + "/api/attendance/time_off_policies"; };

  if (!document.getElementById("screen-topolcfg")) {
    var main = document.createElement("div");
    main.id = "screen-topolcfg"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">⚙️ Timeoff Policy Config</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">⚙️</div><div><div class="mh-title">Time Off Policy</div><div class="mh-sub">Create · Update · View · Delete</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="topolcfg-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet · paycodes master · existing policies · dropdown reference</div></div>' +
        '<div class="bf-action-card" id="topolcfg-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Blank policy ID = create · filled = update</div></div>' +
        '<div class="bf-action-card" id="topolcfg-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Full detail — one row per approval level</div></div>' +
        '<div class="bf-action-card" id="topolcfg-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete policies by comma-separated IDs</div></div>' +
      '</div>' +
      '<div id="topolcfg-tpl-status" class="bf-status" style="margin-top:14px;"></div>';
    modal.appendChild(main);

    var create = document.createElement("div");
    create.id = "screen-topolcfg-create"; create.style.display = "none";
    create.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-topolcfg">⚙️ Timeoff Policy Config</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>' +
      '<div class="bf-info-box">' +
        '<b>id</b> column: blank = create, filled = update.<br>' +
        'Multiple rows with the same id/Name = multiple approval levels for that policy.<br>' +
        '<b>Paycodes</b> / <b>Skip Paycodes</b>: comma-separated ids (e.g. <code>442,443,444</code>).<br>' +
        'Dates are plain <code>YYYY-MM-DD</code>. <b>Approver Type</b> is always sent as <code>ATTRIBUTE</code> regardless of the column.<br>' +
        '<b>Probationary Period</b> fields are optional — leave both blank if the policy doesn\'t use probation.' +
      '</div>' +
      '<div id="topolcfg-create-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="topolcfg-file"><span id="topolcfg-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="topolcfg-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="topolcfg-c-prog"><div class="bf-pb" id="topolcfg-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="topolcfg-create-log"></div>' +
      '<button class="bf-btn bf-success" id="topolcfg-submit" disabled>🚀 Submit Time Off Policies</button>' +
      '<button class="bf-btn bf-outline" id="topolcfg-cancel">✕ Cancel Upload</button>' +
      '<button class="bf-btn bf-outline" id="topolcfg-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="topolcfg-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(create);

    var view = document.createElement("div");
    view.id = "screen-topolcfg-view"; view.style.display = "none";
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-topolcfg">⚙️ Timeoff Policy Config</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>' +
      '<div id="topolcfg-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="topolcfg-v-prog" style="display:none"><div class="bf-pb" id="topolcfg-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="topolcfg-fetch">⬇️ Download Time Off Policies</button>';
    modal.appendChild(view);

    var del = document.createElement("div");
    del.id = "screen-topolcfg-delete"; del.style.display = "none";
    del.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-topolcfg">⚙️ Timeoff Policy Config</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>' +
      '<div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>' +
      '<div id="topolcfg-delete-status" class="bf-status"></div>' +
      '<label class="bf-label">Policy IDs to delete (comma-separated)</label>' +
      '<input type="text" id="topolcfg-del-ids" placeholder="61, 62" />' +
      '<label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="topolcfg-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>' +
      '<div class="bf-log" id="topolcfg-delete-log"></div>' +
      '<button class="bf-btn bf-danger" id="topolcfg-do-delete" style="margin-top:10px;">🗑️ Delete</button>';
    modal.appendChild(del);

    Router.register("screen-topolcfg", "screen-topolcfg-create", "screen-topolcfg-view", "screen-topolcfg-delete");
    [main, create, view, del].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  /**
   * Fetches ALL time off policies, paging through the full result set.
   * This one function feeds BOTH "Download Template" (Existing_Policies_Ref
   * sheet) and "View Existing" — the previous version only fetched a
   * single page (the API paginates by default), so with 90+ real
   * policies most of them were silently missing from both outputs.
   */
  function topolFetchAll(progressCb) {
    var page = 0, size = 200, all = [];
    function nextPage() {
      var url = TOPOL_BASE() + "/?projection=FULL&page=" + page + "&size=" + size;
      return ApiTracker.fetch(url, { headers: apiH() }, "Time Off Policy").then(function (r) {
        if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
        return r.json();
      }).then(function (raw) {
        // Handle both a plain array response (no pagination on this
        // particular deployment) and a Spring-style {content:[...]} page.
        var list = Array.isArray(raw) ? raw : (raw.content || raw.data || []);
        var isPagedArray = !Array.isArray(raw); // a bare array means the API isn't paginating at all
        if (!list.length) return all;
        all = all.concat(list);
        if (progressCb) progressCb(all.length);
        if (!isPagedArray || list.length < size) return all; // bare array (all data already) or last page reached
        page++;
        return nextPage();
      });
    }
    return nextPage();
  }

  document.getElementById("topolcfg-action-tpl").onclick = function () {
    var btn = document.getElementById("topolcfg-action-tpl"); btn.style.opacity = "0.6";
    Notifications.status("topolcfg-tpl-status", "⏳ Fetching all policies (paging)...", "info");
    Promise.all([
      topolFetchAll(function (n) { Notifications.status("topolcfg-tpl-status", "⏳ Fetched " + n + " polic" + (n === 1 ? "y" : "ies") + " so far...", "info"); }).catch(function () { return []; }),
      fetchPaycodesRef().catch(function () { return []; })
    ]).then(function (results) {
      var policies = results[0] || [];
      var paycodes = results[1] || [];
      var existRows = [];
      policies.forEach(function (p) { topolFlattenPolicy(p).forEach(function (row) { existRows.push(row); }); });

      downloadExcel("time_off_policies_template.xlsx", [
        { name: "Upload_Template", tabColor: "7C3AED", headers: TOPOL_HEADERS, rows: [], highlightCols: TOPOL_INPUT_COLS, headerColors: TOPOL_HEADER_COLORS },
        { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "name", "description"], rows: paycodes.map(function (p) { return [p.id, p.code || "", p.description || ""]; }) },
        { name: "Existing_Policies_Ref", tabColor: "0369A1", headers: TOPOL_HEADERS, rows: existRows, headerColors: TOPOL_HEADER_COLORS },
        { name: "Valid_Options", tabColor: "D97706", headers: TOPOL_DROPDOWNS_HEADERS, rows: TOPOL_DROPDOWNS_ROWS }
      ]);
      Notifications.success("topolcfg-tpl-status", "✅ Template downloaded — " + policies.length + " existing polic" + (policies.length === 1 ? "y" : "ies") + " (" + existRows.length + " row(s)), " + paycodes.length + " paycode(s)");
      btn.style.opacity = "1";
    }).catch(function (e) {
      Notifications.error("topolcfg-tpl-status", "❌ " + e.message);
      btn.style.opacity = "1";
    });
  };

  document.getElementById("topolcfg-action-create").onclick = function () {
    Notifications.clearLog("topolcfg-create-log");
    AppState.cache.topolcfgRows = null; AppState.cache.topolcfgSuccessRows = []; AppState.cache.topolcfgFailedRows = [];
    document.getElementById("topolcfg-submit").disabled = true;
    document.getElementById("topolcfg-dl-success").style.display = "none";
    document.getElementById("topolcfg-dl-failed").style.display = "none";
    document.getElementById("topolcfg-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    document.getElementById("topolcfg-file").value = "";
    Router.go("screen-topolcfg-create");
  };
  document.getElementById("topolcfg-action-view").onclick = function () { Router.go("screen-topolcfg-view"); };
  document.getElementById("topolcfg-action-delete").onclick = function () { Notifications.clearLog("topolcfg-delete-log"); Router.go("screen-topolcfg-delete"); };

  // ── Custom file reader: header:1 (array) mode, NOT the shared
  // wireFileInput helper — this sheet has duplicate column names, which
  // would silently collide/lose data under the normal {colName:value}
  // object-keyed reading every other module uses. ──
  document.getElementById("topolcfg-cancel").onclick = function () {
    AppState.cache.topolcfgRows = null;
    document.getElementById("topolcfg-file").value = "";
    document.getElementById("topolcfg-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    document.getElementById("topolcfg-submit").disabled = true;
    Notifications.clearLog("topolcfg-create-log");
    document.getElementById("topolcfg-create-status").className = "bf-status";
    document.getElementById("topolcfg-create-status").textContent = "";
    Router.go("screen-topolcfg");
  };

  document.getElementById("topolcfg-file").addEventListener("change", function (e) {
    var file = e.target.files[0];
    var submitBtn = document.getElementById("topolcfg-submit");
    if (!file) { AppState.cache.topolcfgRows = null; submitBtn.disabled = true; return; }
    document.getElementById("topolcfg-file-name").textContent = "📄 " + file.name;

    var reader = new FileReader();
    reader.onload = function (ev) {
      try {
        var wb = XLSX.read(new Uint8Array(ev.target.result), { type: "array" });
        var ws = wb.Sheets[wb.SheetNames[0]];
        var aoa = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "", raw: false });
        // Drop the header row (row 0) — everything after is data, indexed
        // positionally, exactly matching the C.* constants above.
        var dataRows = aoa.slice(1).filter(function (r) { return r.some(function (c) { return String(c).trim() !== ""; }); });
        AppState.cache.topolcfgRows = dataRows;
        submitBtn.disabled = false;
        if (Audit) Audit.onFileSelected(file.name);
      } catch (err) {
        Notifications.alert("❌ Failed to read file: " + err.message);
        AppState.cache.topolcfgRows = null; submitBtn.disabled = true;
      }
    };
    reader.onerror = function () { Notifications.alert("❌ Failed to read file"); submitBtn.disabled = true; };
    reader.readAsArrayBuffer(file);
  });

  document.getElementById("topolcfg-dl-success").onclick = function () {
    downloadExcel("topolcfg_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["policy_id", "name", "action"], rows: (AppState.cache.topolcfgSuccessRows || []).map(function (r) { return [r.id || "", r.name, r.action]; }) }]);
  };
  document.getElementById("topolcfg-dl-failed").onclick = function () {
    downloadExcel("topolcfg_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["name", "http_status", "error"], rows: (AppState.cache.topolcfgFailedRows || []).map(function (r) { return [r.name, r.status || "", r.error || ""]; }) }]);
  };

  function idList(str) {
    return String(str || "").split(",").map(function (s) { return parseIntSafe(s.trim()); }).filter(function (n) { return n !== null; });
  }

  /** Adds `key` to `obj` only if `rawVal` isn't blank — used so we never
   *  send an empty-string enum or an artificial 0 that trips "min < max"
   *  validation. Mirrors how the API's own GET response omits fields
   *  that don't apply. */
  /** Accepts either ISO (YYYY-MM-DD) or DD-MM-YYYY and always returns
   *  ISO — the API strictly requires ISO (confirmed: your working Postman
   *  example used "2026-08-01"), but typing dates as DD-MM-YYYY in a
   *  spreadsheet is natural, so this auto-detects rather than requiring
   *  one exact format. */
  function topolNormalizeDate(v) {
    if (!v) return "";
    var s = String(v).trim();
    if (/^\d{4}-\d{1,2}-\d{1,2}$/.test(s)) return s; // already ISO
    var p = s.split(/[-\/]/);
    if (p.length === 3 && p[2].length === 4) return p[2] + "-" + ("0" + p[1]).slice(-2) + "-" + ("0" + p[0]).slice(-2); // DD-MM-YYYY
    return s;
  }

  function addIfPresent(obj, key, rawVal, transform) {
    var v = String(rawVal === undefined || rawVal === null ? "" : rawVal).trim();
    if (v === "") return;
    obj[key] = transform ? transform(v) : v;
  }

  function buildPayload(group) {
    var first = group[0];

    // Top-level approvalLevel is the COUNT of approval levels this policy
    // has (confirmed against real data: a policy with 2 approvalConfigs
    // has policy.approvalLevel:"2") — NOT the same as each individual
    // approvalConfigs[].level. Falls back to the highest per-row level
    // typed in, in case rows aren't numbered 1..N sequentially.
    var typedLevels = group.map(function (row) { return parseIntSafe(row[C.APPROVAL_LEVEL]); }).filter(function (v) { return v !== null; });
    var topApprovalLevel = Math.max(group.length, typedLevels.length ? Math.max.apply(null, typedLevels) : 0);

    var ulApplicable = topolToBool(first[C.UL_APPLICABLE]);
    var usageLimit = { applicable: ulApplicable };
    if (ulApplicable) {
      addIfPresent(usageLimit, "count", first[C.UL_COUNT], function (v) { return parseIntSafe(v) || 0; });
      addIfPresent(usageLimit, "period", first[C.UL_PERIOD]);
      addIfPresent(usageLimit, "referenceDate", first[C.UL_REFDATE], topolNormalizeDate);
    }

    var avApplicable = topolToBool(first[C.AV_APPLICABLE]);
    var availingLimit = { applicable: avApplicable };
    if (avApplicable) {
      addIfPresent(availingLimit, "minDays", first[C.AV_MIN], function (v) { return String(parseFloat(v)); });
      addIfPresent(availingLimit, "maxDays", first[C.AV_MAX], function (v) { return String(parseFloat(v)); });
      availingLimit.applyInBlock = topolToBool(first[C.AV_BLOCK]);
    }

    var duApplicable = topolToBool(first[C.DU_APPLICABLE]);
    var documentUpload = { applicable: duApplicable };
    if (duApplicable) {
      addIfPresent(documentUpload, "minDays", first[C.DU_MIN], function (v) { return String(parseFloat(v)); });
      addIfPresent(documentUpload, "maxDays", first[C.DU_MAX], function (v) { return String(parseFloat(v)); });
      addIfPresent(documentUpload, "period", first[C.DU_PERIOD]);
      addIfPresent(documentUpload, "referenceDate", first[C.DU_REFDATE], topolNormalizeDate);
      documentUpload.ignoreSandwichRule = topolToBool(first[C.DU_IGNORE_SANDWICH]);
    }

    var srApplicable = topolToBool(first[C.SR_APPLICABLE]);
    var sandwichRule = { applicable: srApplicable };
    if (srApplicable) {
      addIfPresent(sandwichRule, "beforeDays", first[C.SR_BEFORE], function (v) { return String(parseIntSafe(v) || 0); });
      addIfPresent(sandwichRule, "afterDays", first[C.SR_AFTER], function (v) { return String(parseIntSafe(v) || 0); });
    }

    var payload = {
      name: String(first[C.NAME] || "").trim(),
      description: String(first[C.DESC] || "").trim(),
      paycode: { id: parseIntSafe(first[C.PAYCODE_ID]) },
      paycodeGroup: String(first[C.PAYCODE_GROUP] || "").trim(),
      numOfPastSignedOfPeriods: parseIntSafe(first[C.PAST_SIGNED]) || 1, // API rejects 0 (min constraint)
      considerSignOff: topolToBool(first[C.CONSIDER_SIGNOFF]),
      ignoreSchedulePaycodes: topolToBool(first[C.IGNORE_SCHEDULE_PAYCODES]),
      enableForEmployee: topolToBool(first[C.ENABLE_FOR_EMPLOYEE]),
      approvalLevel: String(topApprovalLevel), // TOP-LEVEL — was missing entirely before
      approverType: "ATTRIBUTE",               // TOP-LEVEL — was missing entirely before
      remarks: String(first[C.REMARKS] || "").trim(),
      notes: String(first[C.NOTES] || "").trim(),
      remarksRequired: topolToBool(first[C.REMARKS_REQUIRED]),
      usageLimits: [usageLimit],
      availingLimit: availingLimit,
      documentUpload: documentUpload,
      sandwichRule: sandwichRule,
      approvalConfigs: group.map(function (row) {
        return {
          level: parseIntSafe(row[C.APPROVAL_LEVEL]) || 1,
          approverType: "ATTRIBUTE", // forced — see file header comment
          approver: String(row[C.APPROVER] || "").trim(),
          sendNotification: topolToBool(row[C.SEND_NOTIFICATION]),
          reminderNotificationDurations: String(row[C.REMINDER_DURATIONS] || "").trim() || "P2D",
          tatDuration: String(row[C.TAT_DURATION] || "").trim() || "P2D",
          tatAction: String(row[C.TAT_ACTION] || "").trim() || "APPROVE",
          sendEmployeeNotification: topolToBool(row[C.SEND_EMP_NOTIFICATION]),
          pushNotification: topolToBool(row[C.PUSH_NOTIFICATION]),
          allowEdit: false,
          enableTatForCancellation: topolToBool(row[C.ENABLE_TAT_CANCEL]),
          enableWorkflowNoEmails: topolToBool(row[C.ENABLE_WORKFLOW_NO_EMAILS])
        };
      })
    };

    var spIds = idList(first[C.PAYCODES]);
    var sspIds = idList(first[C.SKIP_PAYCODES]);
    if (spIds.length) payload.sandwichPaycodes = spIds.map(function (id) { return { id: id }; });
    if (sspIds.length) payload.sandwichSkipPaycodes = sspIds.map(function (id) { return { id: id }; });

    // probationaryPeriod / probationaryPeriodValue: optional, omitted
    // entirely unless actually filled in.
    var probPeriod = String(first[C.PROB_PERIOD] || "").trim();
    if (probPeriod) {
      payload.probationaryPeriod = probPeriod;
      payload.probationaryPeriodValue = parseIntSafe(first[C.PROB_VALUE]) || 1;
    }

    return payload;

  }

  document.getElementById("topolcfg-submit").onclick = function () {
    var btn = document.getElementById("topolcfg-submit");
    var rows = AppState.cache.topolcfgRows || [];
    Notifications.clearLog("topolcfg-create-log");
    document.getElementById("topolcfg-dl-success").style.display = "none";
    document.getElementById("topolcfg-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("topolcfg-create-status", "❌ No data found"); return; }

    var updateGroups = {}, createGroups = {}, parseErrors = [];
    rows.forEach(function (row, i) {
      var policyId = parseIntSafe(row[C.ID]);
      var name = String(row[C.NAME] || "").trim();
      if (!name) { parseErrors.push("Row " + (i + 2) + ": Name is required"); return; }
      if (policyId !== null) { if (!updateGroups[policyId]) updateGroups[policyId] = []; updateGroups[policyId].push(row); }
      else { if (!createGroups[name]) createGroups[name] = []; createGroups[name].push(row); }
    });
    if (parseErrors.length) parseErrors.forEach(function (e) { Notifications.log("topolcfg-create-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });

    var updateEntries = Object.keys(updateGroups).map(function (k) { return [k, updateGroups[k]]; });
    var createEntries = Object.keys(createGroups).map(function (k) { return [k, createGroups[k]]; });
    var total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error("topolcfg-create-status", "❌ No valid groups found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("topolcfg-c-prog");
    AppState.cache.topolcfgSuccessRows = []; AppState.cache.topolcfgFailedRows = [];
    var s = 0, f = 0, done = 0;

    function processUpdate(i) {
      if (i >= updateEntries.length) return processCreate(0);
      var policyId = updateEntries[i][0], group = updateEntries[i][1];
      var payload = buildPayload(group);
      payload.id = parseInt(policyId);
      ApiTracker.fetch(TOPOL_BASE() + "/" + payload.id, { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Time Off Policy").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            Notifications.log("topolcfg-create-log", "✅ Updated: " + payload.name + " (" + payload.approvalConfigs.length + " level(s))", "ok");
            s++; Audit.onDbOp("updated", 1);
            AppState.cache.topolcfgSuccessRows.push({ id: payload.id, name: payload.name, action: "Updated" });
          } else {
            var err = parseApiError(body);
            Notifications.log("topolcfg-create-log", "❌ Failed update: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.topolcfgFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("topolcfg-create-log", "❌ Error: " + payload.name + " — " + e.message, "fail");
        f++; AppState.cache.topolcfgFailedRows.push({ name: payload.name, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("topolcfg-c-bar", (done / total) * 100);
        processUpdate(i + 1);
      });
    }

    function processCreate(i) {
      if (i >= createEntries.length) return finish();
      var name = createEntries[i][0], group = createEntries[i][1];
      var payload = buildPayload(group);
      ApiTracker.fetch(TOPOL_BASE() + "/", { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Time Off Policy").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            Notifications.log("topolcfg-create-log", "✅ Created: " + payload.name + " (" + payload.approvalConfigs.length + " level(s))", "ok");
            s++; Audit.onDbOp("created", 1);
            var createdId = ""; try { createdId = JSON.parse(body).id || ""; } catch (e) {}
            AppState.cache.topolcfgSuccessRows.push({ id: createdId, name: payload.name, action: "Created" });
          } else {
            var err = parseApiError(body);
            Notifications.log("topolcfg-create-log", "❌ Failed create: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.topolcfgFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("topolcfg-create-log", "❌ Error: " + e.message, "fail");
        f++; AppState.cache.topolcfgFailedRows.push({ name: name, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("topolcfg-c-bar", (done / total) * 100);
        processCreate(i + 1);
      });
    }

    function finish() {
      Notifications.log("topolcfg-create-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("topolcfg-create-log", "✅ Success: " + s + "  ❌ Failed: " + f, f === 0 ? "ok" : "info");
      Notifications.status("topolcfg-create-status", "Done — " + s + " success, " + f + " failed", f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Submit Time Off Policies");
      Notifications.progress.hide("topolcfg-c-prog");
      if (AppState.cache.topolcfgSuccessRows.length) document.getElementById("topolcfg-dl-success").style.display = "block";
      if (AppState.cache.topolcfgFailedRows.length) document.getElementById("topolcfg-dl-failed").style.display = "block";
    }

    processUpdate(0);
  };

  document.getElementById("topolcfg-fetch").onclick = function () {
    var btn = document.getElementById("topolcfg-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("topolcfg-v-prog");
    Notifications.info("topolcfg-view-status", "⏳ Fetching time off policies (FULL projection)..."); Notifications.progress.set("topolcfg-v-bar", 20);
    topolFetchAll(function (n) { Notifications.info("topolcfg-view-status", "⏳ Fetched " + n + " polic" + (n === 1 ? "y" : "ies") + " so far (paging)..."); Notifications.progress.set("topolcfg-v-bar", Math.min(20 + n / 2, 55)); }).then(function (policies) {
      if (!policies.length) { Notifications.info("topolcfg-view-status", "ℹ️ No policies found."); return; }
      Notifications.info("topolcfg-view-status", "⏳ Processing " + policies.length + " polic" + (policies.length === 1 ? "y" : "ies") + "..."); Notifications.progress.set("topolcfg-v-bar", 60);
      var rows = [];
      policies.forEach(function (p) { topolFlattenPolicy(p).forEach(function (row) { rows.push(row); }); });
      Notifications.info("topolcfg-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("topolcfg-v-bar", 90);
      downloadExcel("time_off_policies_" + new Date().toISOString().slice(0, 10) + ".xlsx", [{ name: "Time_Off_Policies", tabColor: "7C3AED", headers: TOPOL_HEADERS, rows: rows, headerColors: TOPOL_HEADER_COLORS }]);
      Notifications.progress.set("topolcfg-v-bar", 100);
      Notifications.success("topolcfg-view-status", "✅ Download complete — " + policies.length + " polic" + (policies.length === 1 ? "y" : "ies") + ", " + rows.length + " row(s)");
    }).catch(function (e) {
      Notifications.error("topolcfg-view-status", "❌ " + e.message); Notifications.progress.set("topolcfg-v-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "⬇️ Download Time Off Policies");
      Notifications.progress.hide("topolcfg-v-prog", 2000);
    });
  };

  document.getElementById("topolcfg-do-delete").onclick = function () {
    if (!document.getElementById("topolcfg-confirm").checked) { Notifications.error("topolcfg-delete-status", "⚠️ Check confirmation box"); return; }
    var ids = document.getElementById("topolcfg-del-ids").value.split(",").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    if (!ids.length) { Notifications.error("topolcfg-delete-status", "❌ No IDs entered"); return; }
    var btn = document.getElementById("topolcfg-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("topolcfg-delete-log");
    var s = 0, f = 0;
    function next(i) {
      if (i >= ids.length) {
        Audit.onDbOp("deleted", s);
        Notifications.status("topolcfg-delete-status", "Done — " + s + " deleted, " + f + " failed", f === 0 ? "success" : "info");
        Notifications.doneLoading(btn, "🗑️ Delete");
        return;
      }
      var id = ids[i];
      ApiTracker.fetch(TOPOL_BASE() + "/" + id, { method: "DELETE", headers: apiH() }, "Time Off Policy").then(function (r) {
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("topolcfg-delete-log", "✅ Deleted: " + id, "ok"); s++; next(i + 1); }
        else return r.text().then(function (t) { Notifications.log("topolcfg-delete-log", "❌ Failed: " + id + " — " + parseApiError(t), "fail"); f++; next(i + 1); });
      }).catch(function (e) { Notifications.log("topolcfg-delete-log", "❌ Error: " + id + " — " + e.message, "fail"); f++; next(i + 1); });
    }
    next(0);
  };

  console.log("✅ Time Off Policy module loaded — 44-col detail view, one row per approval level, plain ISO dates");
}