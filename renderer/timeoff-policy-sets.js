/* =========================================================
 * timeoff-policy-sets.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-tops, screen-tops-create, screen-tops-view, screen-tops-delete
 * GET    /api/attendance/time_off_policy_sets?projection=FULL
 * POST   /api/attendance/time_off_policy_sets            (create, NO trailing slash)
 * PUT    /api/attendance/time_off_policy_sets/{id}/      (update, WITH trailing slash)
 * DELETE /api/attendance/time_off_policy_sets/{id}       (NO trailing slash)
 * — all three confirmed against real working examples.
 *
 * Upload columns (Sheet 1): ID, Timeoff Policy Set Name,
 * Timeoff Policy Set description, Timeoff Policy Entry ID, Paycode ID
 *   - blank ID  -> creates a new set (POST)
 *   - filled ID -> updates the existing set (PUT), replacing its
 *                  entries with whatever rows were uploaded for it
 *   - each row becomes one entry: {"id": <Timeoff Policy Entry ID>,
 *                                   "paycode": {"id": <Paycode ID>}}
 *
 * View / "Existing Sets" format — one row per (set, entry), flattened
 * with the underlying time-off-policy's own fields. The approvalConfigs
 * block (level..enableWorkflowNoEmails) is confirmed correct (same
 * shape used by timeoff-policy-config.js). The min/max/sandwich/notice
 * rule blocks and entitlement/notice-period blocks are BEST-GUESS field
 * paths based on column order — if any of those columns come back
 * blank/wrong once you check real data, tell me the exact JSON field
 * name and I'll fix just that one line.
 * ========================================================= */

var TOPS_VIEW_HEADERS = [
  "id", "Timeoff Policy Set", "Timeoff Policy Set description",
  "id", "Timeoff Policy name", "Timeoff Policy Description",
  "id", "considerSignOff", "ignoreSchedulePaycodes", "numOfPastSignedOfPeriods",
  "applicable", "applicable", "minDays", "maxDays", "applyInBlock",
  "applicable", "ignoreSandwichRule", "applicable", "beforeDays", "afterDays",
  "level", "approverType", "approver", "sendNotification", "reminderNotificationDurations",
  "tatAction", "sendEmployeeNotification", "pushNotification", "allowEdit",
  "enableTatForCancellation", "enableWorkflowNoEmails",
  "approvalLevel", "approverType", "remarksRequired", "enableForEmployee",
  "count", "referenceDate", "period", "notes",
  "minDays", "referenceDate", "period", "remarks"
];

var TOPS_UPLOAD_HEADERS = ["ID", "Timeoff Policy Set Name", "Timeoff Policy Set description", "Timeoff Policy Entry ID", "Paycode ID"];
var TOPS_UPLOAD_INPUT_COLS = [1, 3, 4]; // Set Name, Entry ID, Paycode ID

function topsBoolStr(v) { return v ? "TRUE" : "FALSE"; }
function topsVal(v) { return (v === null || v === undefined) ? "" : v; }

/** Flattens ONE set (with its FULL-projection time-off-policy entries)
 *  into one row per entry, matching TOPS_VIEW_HEADERS.
 *  NOTE: field paths for the rule blocks (proration / minMax / sandwich /
 *  notice / entitlement) are best-guess — see file header comment. */
function topsFlattenSet(set) {
  var rows = [];
  var entries = set.entries || [];
  if (!entries.length) {
    rows.push([set.id, set.name || "", set.description || ""].concat(new Array(TOPS_VIEW_HEADERS.length - 3).fill("")));
    return rows;
  }
  entries.forEach(function (e) {
    var cfg = (e.approvalConfigs && e.approvalConfigs[0]) || {};
    var delegation = e.delegationConfig || {};
    var minMax = e.minMaxDaysRule || {};
    var sandwich = e.sandwichRule || {};
    var notice = e.noticeDaysRule || {};
    var entitlement = e.entitlementRule || {};
    var noticePeriod = e.noticePeriodRule || {};
    var paycode = e.paycode || {};

    rows.push([
      set.id, set.name || "", set.description || "",
      e.id || "", e.name || "", e.description || "",
      paycode.id || "",
      topsBoolStr(e.considerSignOff), topsBoolStr(e.ignoreSchedulePaycodes), topsVal(e.numOfPastSignedOfPeriods),
      topsBoolStr(e.prorationApplicable),
      topsBoolStr(minMax.applicable), topsVal(minMax.minDays), topsVal(minMax.maxDays), topsBoolStr(minMax.applyInBlock),
      topsBoolStr(sandwich.applicable), topsBoolStr(sandwich.ignoreSandwichRule),
      topsBoolStr(notice.applicable), topsVal(notice.beforeDays), topsVal(notice.afterDays),
      topsVal(cfg.level), cfg.approverType || "", cfg.approver || "", topsBoolStr(cfg.sendNotification),
      cfg.reminderNotificationDurations || "", cfg.tatAction || "", topsBoolStr(cfg.sendEmployeeNotification),
      topsBoolStr(cfg.pushNotification), topsBoolStr(cfg.allowEdit), topsBoolStr(cfg.enableTatForCancellation), topsBoolStr(cfg.enableWorkflowNoEmails),
      topsVal(delegation.approvalLevel), delegation.approverType || "", topsBoolStr(delegation.remarksRequired), topsBoolStr(delegation.enableForEmployee),
      topsVal(entitlement.count), entitlement.referenceDate || "", entitlement.period || "", entitlement.notes || "",
      topsVal(noticePeriod.minDays), noticePeriod.referenceDate || "", noticePeriod.period || "", noticePeriod.remarks || ""
    ]);
  });
  return rows;
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

  var TOPS_BASE = function () { return AppState.BASE_URL + "/api/attendance/time_off_policy_sets"; };
  var TOPOL_REF = function () { return AppState.BASE_URL + "/api/attendance/time_off_policies"; };

  if (!document.getElementById("screen-tops")) {
    var main = document.createElement("div");
    main.id = "screen-tops"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🏖️ Time Off Policy Set</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">🏖️</div><div><div class="mh-title">Time Off Policy Set</div><div class="mh-sub">Create · View · Delete</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="tops-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet · full existing sets · time off policies master</div></div>' +
        '<div class="bf-action-card" id="tops-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Blank ID = create · filled ID = update</div></div>' +
        '<div class="bf-action-card" id="tops-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Full detail — one row per time off policy entry</div></div>' +
        '<div class="bf-action-card" id="tops-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete sets by comma-separated IDs</div></div>' +
      '</div>';
    modal.appendChild(main);

    var create = document.createElement("div");
    create.id = "screen-tops-create"; create.style.display = "none";
    create.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-tops">🏖️ Time Off Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>' +
      '<div class="bf-info-box">' +
        'Columns: <b>ID</b> (blank = create, filled = update) · <b>Timeoff Policy Set Name</b> · <b>Timeoff Policy Set description</b> · <b>Timeoff Policy Entry ID</b> · <b>Paycode ID</b>.<br>' +
        'Multiple rows with the same ID/Set Name = multiple entries in one set.' +
      '</div>' +
      '<div id="tops-create-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="tops-file"><span id="tops-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="tops-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="tops-c-prog"><div class="bf-pb" id="tops-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="tops-create-log"></div>' +
      '<button class="bf-btn bf-success" id="tops-submit" disabled>🚀 Submit Time Off Policy Sets</button>' +
      '<button class="bf-btn bf-outline" id="tops-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="tops-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(create);

    var view = document.createElement("div");
    view.id = "screen-tops-view"; view.style.display = "none";
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-tops">🏖️ Time Off Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>' +
      '<div id="tops-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="tops-v-prog" style="display:none"><div class="bf-pb" id="tops-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="tops-fetch">⬇️ Download Time Off Policy Sets</button>';
    modal.appendChild(view);

    var del = document.createElement("div");
    del.id = "screen-tops-delete"; del.style.display = "none";
    del.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-tops">🏖️ Time Off Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>' +
      '<div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>' +
      '<div id="tops-delete-status" class="bf-status"></div>' +
      '<label class="bf-label">Set IDs to delete (comma-separated)</label>' +
      '<input type="text" id="tops-del-ids" placeholder="52, 66" />' +
      '<label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="tops-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>' +
      '<div class="bf-log" id="tops-delete-log"></div>' +
      '<button class="bf-btn bf-danger" id="tops-do-delete" style="margin-top:10px;">🗑️ Delete</button>';
    modal.appendChild(del);

    Router.register("screen-tops", "screen-tops-create", "screen-tops-view", "screen-tops-delete");
    [main, create, view, del].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  function topsFetchAllSets() {
    return ApiTracker.fetch(TOPS_BASE() + "?projection=FULL", { headers: apiH() }, "Time Off Policy Set")
      .then(function (r) {
        if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
        return r.json();
      })
      .then(function (raw) { return Array.isArray(raw) ? raw : (raw.content || raw.data || []); });
  }

  document.getElementById("tops-action-tpl").onclick = function () {
    var btn = document.getElementById("tops-action-tpl"); btn.style.opacity = "0.6";
    Promise.all([
      topsFetchAllSets().catch(function () { return []; }),
      ApiTracker.fetch(TOPOL_REF(), { headers: apiH() }, "Time Off Policy Set").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
    ]).then(function (results) {
      var sets = results[0] || [];
      var rawPolicies = results[1] || [];
      var policies = Array.isArray(rawPolicies) ? rawPolicies : (rawPolicies.content || []);
      var existRows = [];
      sets.forEach(function (s) { topsFlattenSet(s).forEach(function (row) { existRows.push(row); }); });

      downloadExcel("time_off_policy_sets_template.xlsx", [
        { name: "Upload_Template", tabColor: "7C3AED", headers: TOPS_UPLOAD_HEADERS, rows: [], highlightCols: TOPS_UPLOAD_INPUT_COLS },
        { name: "Existing_Sets_Full", tabColor: "0369A1", headers: TOPS_VIEW_HEADERS, rows: existRows },
        { name: "Time_Off_Policies_Master", tabColor: "059669", headers: ["id", "name", "description"], rows: policies.map(function (p) { return [p.id, p.name || "", p.description || ""]; }) }
      ]);
      btn.style.opacity = "1";
    });
  };

  document.getElementById("tops-action-create").onclick = function () {
    Notifications.clearLog("tops-create-log");
    AppState.cache.tops = null; AppState.cache.topsSuccessRows = []; AppState.cache.topsFailedRows = [];
    document.getElementById("tops-submit").disabled = true;
    document.getElementById("tops-dl-success").style.display = "none";
    document.getElementById("tops-dl-failed").style.display = "none";
    Router.go("screen-tops-create");
  };
  document.getElementById("tops-action-view").onclick = function () { Router.go("screen-tops-view"); };
  document.getElementById("tops-action-delete").onclick = function () { Notifications.clearLog("tops-delete-log"); Router.go("screen-tops-delete"); };

  wireFileInput("tops-file", "tops-file-name", "tops-submit", "tops");

  document.getElementById("tops-dl-success").onclick = function () {
    downloadExcel("tops_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["set_id", "set_name", "entries_submitted", "action"], rows: (AppState.cache.topsSuccessRows || []).map(function (r) { return [r.id || "", r.name, r.entries, r.action]; }) }]);
  };
  document.getElementById("tops-dl-failed").onclick = function () {
    downloadExcel("tops_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["set_name", "http_status", "error"], rows: (AppState.cache.topsFailedRows || []).map(function (r) { return [r.name, r.status || "", r.error || ""]; }) }]);
  };

  document.getElementById("tops-submit").onclick = function () {
    var btn = document.getElementById("tops-submit");
    var rows = AppState.cache.tops || [];
    Notifications.clearLog("tops-create-log");
    document.getElementById("tops-dl-success").style.display = "none";
    document.getElementById("tops-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("tops-create-status", "❌ No data found"); return; }

    function col(row, name) {
      var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
      return k ? String(row[k] || "").trim() : "";
    }

    var updateGroups = {}, createGroups = {}, parseErrors = [];
    rows.forEach(function (row, i) {
      var setId = parseIntSafe(col(row, "ID"));
      var setName = col(row, "Timeoff Policy Set Name");
      var entryId = parseIntSafe(col(row, "Timeoff Policy Entry ID"));
      var paycodeId = parseIntSafe(col(row, "Paycode ID"));
      if (entryId === null) { parseErrors.push("Row " + (i + 2) + ": Timeoff Policy Entry ID is required/invalid"); return; }
      if (paycodeId === null) { parseErrors.push("Row " + (i + 2) + ": Paycode ID is required/invalid"); return; }
      if (setId !== null) { if (!updateGroups[setId]) updateGroups[setId] = []; updateGroups[setId].push(row); }
      else { if (!setName) { parseErrors.push("Row " + (i + 2) + ": Timeoff Policy Set Name required when ID is blank"); return; } if (!createGroups[setName]) createGroups[setName] = []; createGroups[setName].push(row); }
    });
    if (parseErrors.length) parseErrors.forEach(function (e) { Notifications.log("tops-create-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });

    var updateEntries = Object.keys(updateGroups).map(function (k) { return [k, updateGroups[k]]; });
    var createEntries = Object.keys(createGroups).map(function (k) { return [k, createGroups[k]]; });
    var total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error("tops-create-status", "❌ No valid groups found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("tops-c-prog");
    AppState.cache.topsSuccessRows = []; AppState.cache.topsFailedRows = [];
    var s = 0, f = 0, done = 0;

    function buildEntries(group) {
      var entries = [], seen = {};
      group.forEach(function (row) {
        var entryId = parseIntSafe(col(row, "Timeoff Policy Entry ID"));
        var paycodeId = parseIntSafe(col(row, "Paycode ID"));
        if (entryId === null || paycodeId === null || seen[entryId]) return;
        seen[entryId] = true;
        entries.push({ id: entryId, paycode: { id: paycodeId } });
      });
      return entries;
    }

    function processUpdate(i) {
      if (i >= updateEntries.length) return processCreate(0);
      var setId = updateEntries[i][0], group = updateEntries[i][1], first = group[0];
      var payload = { id: parseInt(setId), name: col(first, "Timeoff Policy Set Name"), description: col(first, "Timeoff Policy Set description") || col(first, "Timeoff Policy Set Name"), entries: buildEntries(group) };
      ApiTracker.fetch(TOPS_BASE() + "/" + payload.id + "/", { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Time Off Policy Set").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            Notifications.log("tops-create-log", "✅ Updated: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("updated", 1);
            AppState.cache.topsSuccessRows.push({ id: payload.id, name: payload.name, entries: payload.entries.length, action: "Updated" });
          } else {
            var err = parseApiError(body);
            Notifications.log("tops-create-log", "❌ Failed update: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.topsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("tops-create-log", "❌ Error: " + payload.name + " — " + e.message, "fail");
        f++; AppState.cache.topsFailedRows.push({ name: payload.name, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("tops-c-bar", (done / total) * 100);
        processUpdate(i + 1);
      });
    }

    function processCreate(i) {
      if (i >= createEntries.length) return finish();
      var setName = createEntries[i][0], group = createEntries[i][1], first = group[0];
      var payload = { name: setName, description: col(first, "Timeoff Policy Set description") || setName, entries: buildEntries(group) };
      ApiTracker.fetch(TOPS_BASE(), { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Time Off Policy Set").then(function (r) {
        return r.text().then(function (body) {
          var createdId = ""; try { createdId = JSON.parse(body).id || ""; } catch (e) {}
          if (r.ok) {
            Notifications.log("tops-create-log", "✅ Created: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("created", 1);
            AppState.cache.topsSuccessRows.push({ id: createdId, name: payload.name, entries: payload.entries.length, action: "Created" });
          } else {
            var err = parseApiError(body);
            Notifications.log("tops-create-log", "❌ Failed create: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.topsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("tops-create-log", "❌ Error: " + e.message, "fail");
        f++; AppState.cache.topsFailedRows.push({ name: setName, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("tops-c-bar", (done / total) * 100);
        processCreate(i + 1);
      });
    }

    function finish() {
      Notifications.log("tops-create-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("tops-create-log", "✅ Success: " + s + "  ❌ Failed: " + f, f === 0 ? "ok" : "info");
      Notifications.status("tops-create-status", "Done — " + s + " success, " + f + " failed", f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Submit Time Off Policy Sets");
      Notifications.progress.hide("tops-c-prog");
      if (AppState.cache.topsSuccessRows.length) document.getElementById("tops-dl-success").style.display = "block";
      if (AppState.cache.topsFailedRows.length) document.getElementById("tops-dl-failed").style.display = "block";
    }

    processUpdate(0);
  };

  document.getElementById("tops-fetch").onclick = function () {
    var btn = document.getElementById("tops-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("tops-v-prog");
    Notifications.info("tops-view-status", "⏳ Fetching time off policy sets (FULL projection)..."); Notifications.progress.set("tops-v-bar", 20);
    topsFetchAllSets().then(function (sets) {
      if (!sets.length) { Notifications.info("tops-view-status", "ℹ️ No sets found."); return; }
      Notifications.info("tops-view-status", "⏳ Processing " + sets.length + " set(s)..."); Notifications.progress.set("tops-v-bar", 60);
      var rows = [];
      sets.forEach(function (s) { topsFlattenSet(s).forEach(function (row) { rows.push(row); }); });
      Notifications.info("tops-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("tops-v-bar", 90);
      downloadExcel("time_off_policy_sets_" + new Date().toISOString().slice(0, 10) + ".xlsx", [{ name: "Time_Off_Policy_Sets", tabColor: "7C3AED", headers: TOPS_VIEW_HEADERS, rows: rows }]);
      Notifications.progress.set("tops-v-bar", 100);
      Notifications.success("tops-view-status", "✅ Download complete — " + sets.length + " set(s), " + rows.length + " row(s)");
    }).catch(function (e) {
      Notifications.error("tops-view-status", "❌ " + e.message); Notifications.progress.set("tops-v-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "⬇️ Download Time Off Policy Sets");
      Notifications.progress.hide("tops-v-prog", 2000);
    });
  };

  document.getElementById("tops-do-delete").onclick = function () {
    if (!document.getElementById("tops-confirm").checked) { Notifications.error("tops-delete-status", "⚠️ Check confirmation box"); return; }
    var ids = document.getElementById("tops-del-ids").value.split(",").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    if (!ids.length) { Notifications.error("tops-delete-status", "❌ No IDs entered"); return; }
    var btn = document.getElementById("tops-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("tops-delete-log");
    var s = 0, f = 0;
    function next(i) {
      if (i >= ids.length) {
        Audit.onDbOp("deleted", s);
        Notifications.status("tops-delete-status", "Done — " + s + " deleted, " + f + " failed", f === 0 ? "success" : "info");
        Notifications.doneLoading(btn, "🗑️ Delete");
        return;
      }
      var id = ids[i];
      ApiTracker.fetch(TOPS_BASE() + "/" + id, { method: "DELETE", headers: apiH() }, "Time Off Policy Set").then(function (r) {
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("tops-delete-log", "✅ Deleted: " + id, "ok"); s++; next(i + 1); }
        else return r.text().then(function (t) { Notifications.log("tops-delete-log", "❌ Failed: " + id + " — " + parseApiError(t), "fail"); f++; next(i + 1); });
      }).catch(function (e) { Notifications.log("tops-delete-log", "❌ Error: " + id + " — " + e.message, "fail"); f++; next(i + 1); });
    }
    next(0);
  };

  console.log("✅ Time Off Policy Set module loaded — full detail view · simplified 5-col upload");
}