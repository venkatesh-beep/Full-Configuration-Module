/* =========================================================
 * accrual-balances.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Owns: screen-acgr, screen-acgr-run
 * GET /api/attendance/accruals/balances_v2?employeeId.equals={id}&effectiveDate={YYYY-MM-DD}
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */

var ACGR_REPORT_HEADERS = [
  "employeeId", "accrualId", "balance", "expired", "totalBalance",
  "granted", "asOnDate", "reserved", "openingBalance", "carryForward", "availed"
];

function acgrFmtDate(d) {
  if (!d) return "";
  var p = String(d).split("-");
  if (p.length === 3 && p[0].length === 4) return p[2] + "-" + p[1] + "-" + p[0];
  return d;
}

function acgrFlatBalance(b) {
  function ts(v) { return (v === null || v === undefined) ? 0 : v; }
  return [
    b.employeeId || "", b.accrualId || "",
    ts(b.balance), ts(b.expired),
    ts(b.totalBalance), ts(b.granted),
    acgrFmtDate(b.asOnDate || ""),
    ts(b.reserved), ts(b.openingBalance),
    ts(b.carryForward), ts(b.availed)
  ];
}

function init(ctx) {
  var AppState = ctx.AppState;
  var apiH = ctx.apiH;
  var downloadExcel = ctx.downloadExcel;
  var wireFileInput = ctx.wireFileInput;
  var parseApiError = ctx.parseApiError;
  var parseIntSafe = ctx.parseIntSafe;
  var Notifications = ctx.Notifications;
  var Router = ctx.Router;
  var Audit = ctx.Audit;
  var ApiTracker = ctx.ApiTracker;
  var modal = ctx.modal;

  var ACGR_EMP_URL = function () { return AppState.BASE_URL + "/api/attendance/employees/"; };
  var ACGR_ACR_URL = function () { return AppState.BASE_URL + "/api/attendance/accruals/"; };
  var ACGR_BAL_URL = function (empId, date) {
    return AppState.BASE_URL + "/api/attendance/accruals/balances_v2?employeeId.equals=" + empId + "&effectiveDate=" + date;
  };

  function acgrFetchEmployees(progressCb) {
    var page = 0, size = 500, all = [];
    function nextPage() {
      return ApiTracker.fetch(ACGR_EMP_URL() + "?page=" + page + "&size=" + size, { headers: apiH() }, "Accrual Balances")
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

  function acgrFetchBalances(empIds, date, progressCb) {
    var BATCH = 10;
    var results = [];
    var done = 0;
    function nextBatch(i) {
      if (i >= empIds.length) return results;
      var batch = empIds.slice(i, i + BATCH);
      var settled = batch.map(function (id) {
        return ApiTracker.fetch(ACGR_BAL_URL(id, date), { headers: apiH() }, "Accrual Balances")
          .then(function (r) { return r.ok ? r.json() : null; })
          .catch(function () { return null; });
      });
      return Promise.all(settled.map(function (p) { return p.then(function (v) { return { ok: true, v: v }; }, function (e) { return { ok: false, v: null }; }); })).then(function (arr) {
        arr.forEach(function (r) {
          var raw = r.ok ? r.v : null;
          var list = Array.isArray(raw) ? raw : (raw && (raw.data || raw.balances)) || [];
          list.forEach(function (b) { results.push(b); });
        });
        done += batch.length;
        if (progressCb) progressCb(done, empIds.length);
        return nextBatch(i + BATCH);
      });
    }
    return nextBatch(0);
  }

  if (!document.getElementById("screen-acgr")) {
    var main = document.createElement("div");
    main.id = "screen-acgr"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📊 Accrual Balances</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">📊</div><div>' +
        '<div class="mh-title">Accrual Balances</div>' +
        '<div class="mh-sub">Select date · Upload IDs or run for all employees · Auto-download report</div>' +
      '</div></div>' +
      '<div class="bf-section-label">Effective Date</div>' +
      '<div style="display:flex;gap:10px;align-items:center;margin-bottom:16px;">' +
        '<input type="date" id="acgr-date" style="flex:1;padding:9px 12px;border:1.5px solid #D1D5DB;border-radius:8px;font-size:13px;" />' +
        '<span style="font-size:12px;color:#6B7280">Leave blank to use today</span>' +
      '</div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="acgr-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Sheet 1: employeeId upload · Sheet 2: employees · Sheet 3: accruals</div></div>' +
        '<div class="bf-action-card" id="acgr-action-upload"><div class="ac-icon">📤</div><div class="ac-name">Upload IDs & Get Report</div><div class="ac-desc">Upload file with employeeId column, fetch balances for each</div></div>' +
        '<div class="bf-action-card" id="acgr-action-all"><div class="ac-icon">🌐</div><div class="ac-name">Run for ALL Employees</div><div class="ac-desc">Auto-fetches all employees, runs balances, downloads report</div></div>' +
      '</div>';
    modal.appendChild(main);

    var run = document.createElement("div");
    run.id = "screen-acgr-run"; run.style.display = "none";
    run.innerHTML =
      '<div class="bf-breadcrumb">' +
        '<span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span>' +
        '<span class="bc-link" data-go="screen-acgr">📊 Accrual Balances</span><span class="bc-sep">›</span>' +
        '<span class="bc-cur" id="acgr-run-title">Upload & Run</span>' +
      '</div>' +
      '<div class="bf-info-box">' +
        'Effective date: <b id="acgr-run-date-label">—</b><br>' +
        'Upload a file with an <b>employeeId</b> column. One employee per row.<br>' +
        '<span id="acgr-run-sub">Each employee\'s balances are fetched concurrently (10 at a time).</span>' +
      '</div>' +
      '<div id="acgr-file-wrap">' +
        '<label class="bf-file-label" for="acgr-file"><span id="acgr-file-name">📂 Click to select file (.xlsx)</span></label>' +
        '<input type="file" id="acgr-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '</div>' +
      '<div id="acgr-run-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="acgr-prog"><div class="bf-pb" id="acgr-bar" style="width:0%"></div></div>' +
      '<div id="acgr-run-counter" style="font-size:12px;color:#6B7280;text-align:center;margin-top:4px;"></div>' +
      '<button class="bf-btn bf-success" id="acgr-submit">🚀 Fetch Balances & Download</button>';
    modal.appendChild(run);

    Router.register("screen-acgr", "screen-acgr-run");
    [main, run].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  function acgrGetDate() {
    var v = document.getElementById("acgr-date") && document.getElementById("acgr-date").value;
    if (v) return v;
    return new Date().toISOString().slice(0, 10);
  }

  document.getElementById("acgr-action-tpl").onclick = function () {
    var btn = document.getElementById("acgr-action-tpl"); btn.style.opacity = "0.6";
    Notifications.status("acgr-run-status", "⏳ Building template...", "info");
    Promise.all([
      acgrFetchEmployees(null).catch(function () { return []; }),
      ApiTracker.fetch(ACGR_ACR_URL(), { headers: apiH() }, "Accrual Balances").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
    ]).then(function (results) {
      var employees = results[0] || [];
      var acrRaw = results[1] || [];
      var accruals = Array.isArray(acrRaw) ? acrRaw : (acrRaw.content || []);
      downloadExcel("accrual_balances_template.xlsx", [
        { name: "Employee_IDs_Upload", tabColor: "1D4ED8", headers: ["employeeId"], rows: [], highlightCols: [0] },
        { name: "Employees_Master", tabColor: "059669", headers: ["id", "externalNumber", "name"], rows: employees.map(function (e) { return [e.id || "", e.externalNumber || "", e.name || e.fullName || ""]; }) },
        { name: "Accruals_Master", tabColor: "7C3AED", headers: ["id", "name", "description"], rows: accruals.map(function (a) { return [a.id || "", a.name || "", a.description || ""]; }) }
      ]);
    }).catch(function (e) {
      Notifications.alert("❌ Template error: " + e.message);
    }).then(function () { btn.style.opacity = "1"; });
  };

  document.getElementById("acgr-action-upload").onclick = function () {
    AppState.cache.acgrFile = null;
    document.getElementById("acgr-run-title").textContent = "Upload IDs & Get Report";
    document.getElementById("acgr-run-sub").textContent = "Each employee's balances are fetched concurrently (10 at a time).";
    document.getElementById("acgr-file-wrap").style.display = "block";
    document.getElementById("acgr-submit").disabled = true;
    document.getElementById("acgr-file-name").textContent = "📂 Click to select file (.xlsx)";
    document.getElementById("acgr-run-date-label").textContent = acgrGetDate();
    document.getElementById("acgr-run-status").className = "bf-status";
    document.getElementById("acgr-run-status").textContent = "";
    document.getElementById("acgr-run-counter").textContent = "";
    document.getElementById("acgr-bar").style.width = "0%";
    Router.go("screen-acgr-run");
  };

  document.getElementById("acgr-action-all").onclick = function () {
    AppState.cache.acgrFile = null;
    document.getElementById("acgr-run-title").textContent = "Run for ALL Employees";
    document.getElementById("acgr-run-sub").textContent = "All employees will be fetched automatically. No file upload needed.";
    document.getElementById("acgr-file-wrap").style.display = "none";
    document.getElementById("acgr-submit").disabled = false;
    document.getElementById("acgr-run-date-label").textContent = acgrGetDate();
    document.getElementById("acgr-run-status").className = "bf-status";
    document.getElementById("acgr-run-status").textContent = "";
    document.getElementById("acgr-run-counter").textContent = "";
    document.getElementById("acgr-bar").style.width = "0%";
    Router.go("screen-acgr-run");
  };

  wireFileInput("acgr-file", "acgr-file-name", "acgr-submit", "acgrFile");

  document.getElementById("acgr-submit").onclick = function () {
    var btn = document.getElementById("acgr-submit");
    var date = acgrGetDate();
    var ctr = document.getElementById("acgr-run-counter");
    var isAllMode = document.getElementById("acgr-file-wrap").style.display === "none";

    btn.disabled = true;
    Notifications.status("acgr-run-status", "⏳ Starting...", "info");
    Notifications.progress.show("acgr-prog");
    Notifications.progress.set("acgr-bar", 0);

    var empIdsPromise;
    if (isAllMode) {
      Notifications.status("acgr-run-status", "⏳ Fetching all employees (paging)...", "info");
      empIdsPromise = acgrFetchEmployees(function (n) { ctr.textContent = "Employees loaded: " + n; }).then(function (employees) {
        return employees.map(function (e) { return e.id; }).filter(Boolean);
      });
    } else {
      var rows = AppState.cache.acgrFile || [];
      if (!rows.length) { Notifications.error("acgr-run-status", "❌ No data in file"); btn.disabled = false; return; }
      function col(row, name) {
        var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
        return k ? String(row[k] || "").trim() : "";
      }
      var ids = [];
      rows.forEach(function (row) {
        var id = parseIntSafe(col(row, "employeeId") || col(row, "employeeid") || col(row, "id"));
        if (id !== null) ids.push(id);
      });
      if (!ids.length) { Notifications.error("acgr-run-status", "❌ No valid employee IDs found in file"); btn.disabled = false; return; }
      Notifications.status("acgr-run-status", "⏳ " + ids.length + " employee(s) found. Fetching balances...", "info");
      empIdsPromise = Promise.resolve(ids);
    }

    empIdsPromise.then(function (empIds) {
      Notifications.progress.set("acgr-bar", 15);
      return acgrFetchBalances(empIds, date, function (done, total) {
        var pct = Math.round(15 + (done / total) * 75);
        Notifications.progress.set("acgr-bar", pct);
        ctr.textContent = "Processed: " + done + " / " + total + " employees";
        Notifications.loading(btn, done + "/" + total + " employees...");
      }).then(function (allBalances) {
        Notifications.progress.set("acgr-bar", 90);
        Notifications.status("acgr-run-status", "⏳ Building Excel...", "info");
        ctr.textContent = "Total balance records: " + allBalances.length;

        if (!allBalances.length) {
          Notifications.status("acgr-run-status", "ℹ️ No balance records returned for the selected employees and date.", "info");
          Notifications.progress.set("acgr-bar", 100);
          Notifications.doneLoading(btn, "🚀 Fetch Balances & Download");
          return;
        }

        return Promise.all([
          acgrFetchEmployees(null).catch(function () { return []; }),
          ApiTracker.fetch(ACGR_ACR_URL(), { headers: apiH() }, "Accrual Balances").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
        ]).then(function (results) {
          var employees = results[0] || [];
          var acrRaw = results[1] || [];
          var accruals = Array.isArray(acrRaw) ? acrRaw : (acrRaw.content || []);

          var balRows = allBalances.map(function (b) { return acgrFlatBalance(b); });
          var dateStr = acgrFmtDate(date).replace(/-/g, "");

          downloadExcel("accrual_balances_" + dateStr + ".xlsx", [
            { name: "Accrual_Balances", tabColor: "1D4ED8", headers: ACGR_REPORT_HEADERS, rows: balRows },
            { name: "Employees_Master", tabColor: "059669", headers: ["id", "externalNumber", "name"], rows: employees.map(function (e) { return [e.id || "", e.externalNumber || "", e.name || e.fullName || ""]; }) },
            { name: "Accruals_Master", tabColor: "7C3AED", headers: ["id", "name", "description"], rows: accruals.map(function (a) { return [a.id || "", a.name || "", a.description || ""]; }) }
          ]);

          Notifications.progress.done("acgr-bar");
          Notifications.status("acgr-run-status", "✅ Download complete — " + balRows.length + " balance record(s) for " + empIds.length + " employee(s) · date: " + acgrFmtDate(date), "success");
          ctr.textContent = "";
        });
      });
    }).catch(function (e) {
      Notifications.error("acgr-run-status", "❌ " + e.message);
      Notifications.progress.set("acgr-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "🚀 Fetch Balances & Download");
      Notifications.progress.hide("acgr-prog", 3000);
    });
  };

  console.log("✅ Accrual Balances module loaded — effectiveDate · Upload IDs · Run All · 3-sheet report");
}
