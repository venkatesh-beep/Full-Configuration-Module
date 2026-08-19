/* =========================================================
 * timeoff-raise.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-tor, screen-tor-upload
 * POST /api/chatbot/timeoff_processes/
 *   Body: {"action":"SUBMIT","employeeNumber":"3475","paycode":"WFH",
 *          "startDate":"06-08-2026","endDate":"06-08-2026","remarks":"Leave"}
 * — dates pass straight through as DD-MM-YYYY, no conversion needed.
 * employeeNumber and paycode are sent exactly as typed (strings, no
 * lookup/parsing) — paycode is the paycode CODE (e.g. "WFH"), not an id.
 *
 * Upload columns: Employee Number, Paycode, Start date, End date, remarks
 * Template also includes reference sheets:
 *   Sheet 2 — Paycodes:  id, paycode name (code), description
 *   Sheet 3 — Employees: id, external number, name
 * ========================================================= */

var TOR_UPLOAD_HEADERS = ["Employee Number", "Paycode", "Start date", "End date", "remarks"];
var TOR_UPLOAD_INPUT_COLS = [0, 1, 2, 3, 4];

function init(ctx) {
  var AppState = ctx.AppState;
  var apiH = ctx.apiH;
  var downloadExcel = ctx.downloadExcel;
  var wireFileInput = ctx.wireFileInput;
  var parseApiError = ctx.parseApiError;
  var fetchPaycodesRef = ctx.fetchPaycodesRef;
  var Notifications = ctx.Notifications;
  var Router = ctx.Router;
  var Audit = ctx.Audit;
  var ApiTracker = ctx.ApiTracker;
  var modal = ctx.modal;

  var TOR_SUBMIT_URL = function () { return AppState.BASE_URL + "/api/attendance/chatbot/timeoff_processes/"; };
  var TOR_EMP_URL = function () { return AppState.BASE_URL + "/api/attendance/employees/"; };

  if (!document.getElementById("screen-tor")) {
    var main = document.createElement("div");
    main.id = "screen-tor"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🙋 Timeoff Raise</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">🙋</div><div><div class="mh-title">Timeoff Raise</div><div class="mh-sub">Bulk-submit time off requests via the chatbot API</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="tor-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet · paycodes reference · employees reference</div></div>' +
        '<div class="bf-action-card" id="tor-action-upload"><div class="ac-icon">📤</div><div class="ac-name">Upload & Submit</div><div class="ac-desc">One row per timeoff request</div></div>' +
      '</div>';
    modal.appendChild(main);

    var upload = document.createElement("div");
    upload.id = "screen-tor-upload"; upload.style.display = "none";
    upload.innerHTML =
      '<div class="bf-breadcrumb">' +
        '<span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span>' +
        '<span class="bc-link" data-go="screen-tor">🙋 Timeoff Raise</span><span class="bc-sep">›</span>' +
        '<span class="bc-cur">Upload & Submit</span>' +
      '</div>' +
      '<div class="bf-info-box">' +
        'Columns: <b>Employee Number</b> · <b>Paycode</b> (the paycode code, e.g. <code>WFH</code>) · ' +
        '<b>Start date</b> · <b>End date</b> (DD-MM-YYYY) · <b>remarks</b>.<br>' +
        'Each row → one <code>POST /api/chatbot/timeoff_processes/</code> with <code>action:"SUBMIT"</code>.' +
      '</div>' +
      '<div id="tor-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="tor-file"><span id="tor-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="tor-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="tor-prog"><div class="bf-pb" id="tor-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="tor-log"></div>' +
      '<button class="bf-btn bf-success" id="tor-submit" disabled>🚀 Submit Timeoff Requests</button>' +
      '<button class="bf-btn bf-outline" id="tor-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="tor-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(upload);

    Router.register("screen-tor", "screen-tor-upload");
    [main, upload].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  /** Pages through GET /api/attendance/employees/ collecting id,
   *  externalNumber, name for the reference sheet. */
  function torFetchAllEmployees(progressCb) {
    var page = 0, size = 500, all = [];
    function nextPage() {
      return ApiTracker.fetch(TOR_EMP_URL() + "?page=" + page + "&size=" + size, { headers: apiH() }, "Timeoff Raise")
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (data) {
          var list = Array.isArray(data) ? data : (data.content || data.data || []);
          if (!list.length) return all;
          all = all.concat(list);
          if (progressCb) progressCb(all.length);
          if (list.length < size) return all;
          page++;
          return nextPage();
        })
        .catch(function () { return all; });
    }
    return nextPage();
  }

  document.getElementById("tor-action-tpl").onclick = function () {
    var btn = document.getElementById("tor-action-tpl"); btn.style.opacity = "0.6";
    Notifications.status("tor-status", "⏳ Building template...", "info");
    Promise.all([
      fetchPaycodesRef().catch(function () { return []; }),
      torFetchAllEmployees(function (n) { Notifications.status("tor-status", "⏳ Loading employees... " + n + " so far", "info"); }).catch(function () { return []; })
    ]).then(function (results) {
      var paycodes = results[0] || [];
      var employees = results[1] || [];

      downloadExcel("timeoff_raise_template.xlsx", [
        { name: "Upload_Template", tabColor: "0EA5E9", headers: TOR_UPLOAD_HEADERS, rows: [], highlightCols: TOR_UPLOAD_INPUT_COLS },
        { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "paycode name", "description"], rows: paycodes.map(function (p) { return [p.id, p.code || "", p.description || ""]; }) },
        { name: "Employees_Master", tabColor: "7C3AED", headers: ["id", "external number", "name"], rows: employees.map(function (e) { return [e.id, e.externalNumber || "", e.name || e.fullName || ""]; }) }
      ]);
      Notifications.status("tor-status", "✅ Template downloaded", "success");
    }).catch(function (e) {
      Notifications.error("tor-status", "❌ Template error: " + e.message);
    }).then(function () { btn.style.opacity = "1"; });
  };

  document.getElementById("tor-action-upload").onclick = function () {
    Notifications.clearLog("tor-log");
    AppState.cache.tor = null; AppState.cache.torSuccessRows = []; AppState.cache.torFailedRows = [];
    document.getElementById("tor-submit").disabled = true;
    document.getElementById("tor-dl-success").style.display = "none";
    document.getElementById("tor-dl-failed").style.display = "none";
    document.getElementById("tor-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    Router.go("screen-tor-upload");
  };

  wireFileInput("tor-file", "tor-file-name", "tor-submit", "tor");

  document.getElementById("tor-dl-success").onclick = function () {
    downloadExcel("timeoff_raise_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["Employee Number", "Paycode", "Start date", "End date", "remarks"],
      rows: (AppState.cache.torSuccessRows || []).map(function (r) { return [r.emp, r.paycode, r.start, r.end, r.remarks]; })
    }]);
  };
  document.getElementById("tor-dl-failed").onclick = function () {
    downloadExcel("timeoff_raise_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["Employee Number", "Paycode", "Start date", "End date", "remarks", "error"],
      rows: (AppState.cache.torFailedRows || []).map(function (r) { return [r.emp, r.paycode, r.start, r.end, r.remarks, r.error || ""]; })
    }]);
  };

  var TOR_MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

  /**
   * Excel silently auto-converts anything that looks like a date into a
   * real date value — depending on regional settings, typing "01-07-2026"
   * can come back out of the workbook as "7/1/2026", "1-Jul-26", or an
   * ISO string, none of which match the API's required DD-MM-YYYY. This
   * normalizes whatever format shows up back into DD-MM-YYYY reliably.
   */
  function torNormalizeDate(val) {
    if (!val) return "";
    var s = String(val).trim();

    if (/^\d{2}-\d{2}-\d{4}$/.test(s)) return s; // already DD-MM-YYYY

    var iso = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/); // YYYY-MM-DD
    if (iso) return ("0" + iso[3]).slice(-2) + "-" + ("0" + iso[2]).slice(-2) + "-" + iso[1];

    var us = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/); // M/D/YYYY (Excel US default)
    if (us) return ("0" + us[2]).slice(-2) + "-" + ("0" + us[1]).slice(-2) + "-" + us[3];

    var dmy = s.match(/^(\d{1,2})-(\d{1,2})-(\d{4})$/); // D-M-YYYY (single-digit day/month)
    if (dmy) return ("0" + dmy[1]).slice(-2) + "-" + ("0" + dmy[2]).slice(-2) + "-" + dmy[3];

    var monMatch = s.match(/^(\d{1,2})-([A-Za-z]{3,})-(\d{2,4})$/); // D-MMM-YY(YY), e.g. "1-Jul-26"
    if (monMatch) {
      var mon = TOR_MONTHS[monMatch[2].slice(0, 3).toLowerCase()];
      if (mon) {
        var yr = monMatch[3].length === 2 ? ("20" + monMatch[3]) : monMatch[3];
        return ("0" + monMatch[1]).slice(-2) + "-" + ("0" + mon).slice(-2) + "-" + yr;
      }
    }

    var d = new Date(s); // last resort — let the browser try
    if (!isNaN(d.getTime())) {
      return ("0" + d.getDate()).slice(-2) + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + d.getFullYear();
    }
    return s; // give up — pass through unchanged so the failure log shows exactly what was sent
  }

  function col(row, name) {
    var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
    return k ? String(row[k] || "").trim() : "";
  }

  document.getElementById("tor-submit").onclick = function () {
    var btn = document.getElementById("tor-submit");
    var rows = AppState.cache.tor || [];
    Notifications.clearLog("tor-log");
    document.getElementById("tor-dl-success").style.display = "none";
    document.getElementById("tor-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("tor-status", "❌ No data found in file"); return; }

    var parseErrors = [], validRows = [];
    rows.forEach(function (row, i) {
      var emp = col(row, "Employee Number");
      var paycode = col(row, "Paycode");
      var start = torNormalizeDate(col(row, "Start date"));
      var end = torNormalizeDate(col(row, "End date"));
      var remarks = col(row, "remarks");
      if (!emp || !paycode || !start || !end) {
        parseErrors.push("Row " + (i + 2) + ": Employee Number, Paycode, Start date and End date are all required");
        return;
      }
      validRows.push({ emp: emp, paycode: paycode, start: start, end: end, remarks: remarks });
    });
    if (parseErrors.length) parseErrors.forEach(function (e) { Notifications.log("tor-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });
    if (!validRows.length) { Notifications.error("tor-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, "Submitting 0/" + validRows.length + "...");
    Notifications.progress.show("tor-prog");
    AppState.cache.torSuccessRows = []; AppState.cache.torFailedRows = [];
    var s = 0, f = 0;

    function next(i) {
      if (i >= validRows.length) return finish();
      var row = validRows[i];
      var body = { action: "SUBMIT", employeeNumber: row.emp, paycode: row.paycode, startDate: row.start, endDate: row.end, remarks: row.remarks };

      ApiTracker.fetch(TOR_SUBMIT_URL(), { method: "POST", headers: apiH(), body: JSON.stringify(body) }, "Timeoff Raise").then(function (r) {
        return r.text().then(function (respBody) {
          if (r.status === 200 || r.status === 201 || r.status === 202) {
            Notifications.log("tor-log", "✅ Submitted — emp: " + row.emp + " | " + row.paycode + " | " + row.start + " to " + row.end, "ok");
            AppState.cache.torSuccessRows.push(row);
            Audit.onDbOp("created", 1);
            s++;
          } else {
            var err = parseApiError(respBody);
            Notifications.log("tor-log", "❌ Failed (HTTP " + r.status + ") — emp: " + row.emp + " | " + err, "fail");
            AppState.cache.torFailedRows.push(Object.assign({}, row, { error: err }));
            f++;
          }
        });
      }).catch(function (e) {
        Notifications.log("tor-log", "❌ Error — emp: " + row.emp + " | " + e.message, "fail");
        AppState.cache.torFailedRows.push(Object.assign({}, row, { error: e.message }));
        f++;
      }).then(function () {
        Notifications.progress.set("tor-bar", ((i + 1) / validRows.length) * 100);
        Notifications.loading(btn, "Submitting " + (i + 1) + "/" + validRows.length + "...");
        next(i + 1);
      });
    }

    function finish() {
      Notifications.progress.done("tor-bar");
      Notifications.log("tor-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("tor-log", "✅ Success: " + s + "  ❌ Failed: " + f + (parseErrors.length ? "  ⚠️ Skipped: " + parseErrors.length : ""), f === 0 ? "ok" : "info");
      Notifications.status("tor-status", "Done — " + s + " submitted, " + f + " failed" + (parseErrors.length ? ", " + parseErrors.length + " skipped" : ""), f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Submit Timeoff Requests");
      Notifications.progress.hide("tor-prog", 2500);
      if (AppState.cache.torSuccessRows.length) document.getElementById("tor-dl-success").style.display = "block";
      if (AppState.cache.torFailedRows.length) document.getElementById("tor-dl-failed").style.display = "block";
    }

    next(0);
  };

  console.log("✅ Timeoff Raise module loaded — bulk POST /api/chatbot/timeoff_processes/");
}