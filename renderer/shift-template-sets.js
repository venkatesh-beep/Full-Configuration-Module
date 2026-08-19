/* =========================================================
 * shift-template-sets.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-sts, screen-sts-create, screen-sts-view, screen-sts-delete
 * GET    /api/attendance/shift_template_sets?projection=FULL
 * POST   /api/attendance/shift_template_sets/          (create)
 * PUT    /api/attendance/shift_template_sets/{id}      (update)
 * DELETE /api/attendance/shift_template_sets/{id}
 *
 * Upload columns (Sheet 1): set_id, set_name, set_description, entry_id
 *   - entry_id is the shift_template id to attach to this set.
 *   - blank set_id  -> creates a new set (POST)
 *   - filled set_id -> updates the existing set (PUT), replacing its
 *                      entries with whatever rows were uploaded for it
 *   - No "priority" column, no separate "shift_template_id" column —
 *     entry_id IS the shift template reference.
 *
 * View / "Existing Sets" format (Sheet 2 of the template, and the
 * View Existing download) — one row per (set, entry), fully flattened
 * with the shift template's own fields:
 *   id, name, description,            (the SET)
 *   id, name, description,            (the SHIFT TEMPLATE)
 *   Start Time, End Time, Start day, End Day,
 *   beforeStartToleranceMinute, afterStartToleranceMinute,
 *   lateInToleranceMinute, earlyOutToleranceMinute,
 *   report, monday, tuesday, wednesday, thursday, friday, saturday, sunday
 * ========================================================= */

var STS_VIEW_HEADERS = [
  "id", "name", "description",
  "id", "name", "description",
  "Start Time", "End Time", "Start day", "End Day",
  "beforeStartToleranceMinute", "afterStartToleranceMinute",
  "lateInToleranceMinute", "earlyOutToleranceMinute",
  "report", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
];

var STS_UPLOAD_HEADERS = ["set_id", "set_name", "set_description", "entry_id"];
var STS_UPLOAD_INPUT_COLS = [1, 3]; // set_name, entry_id are the ones people actually fill in

function stsFmtTime(dt) {
  if (!dt) return "";
  var parts = String(dt).split(" ");
  return parts.length > 1 ? parts[1].slice(0, 5) : String(dt).slice(0, 5);
}
function stsFmtDay(dt) {
  if (!dt) return 1;
  return String(dt).split(" ")[0].slice(-2) === "02" ? 2 : 1;
}
function stsBoolStr(v) { return v ? "TRUE" : "FALSE"; }

/** Flattens ONE set (with its FULL-projection shiftTemplate entries) into
 *  one row per entry, matching STS_VIEW_HEADERS exactly. */
function stsFlattenSet(set) {
  var rows = [];
  var entries = set.entries || [];
  if (!entries.length) {
    rows.push([set.id, set.name || "", set.description || "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]);
    return rows;
  }
  entries.forEach(function (entry) {
    var t = entry.shiftTemplate || {};
    rows.push([
      set.id, set.name || "", set.description || "",
      t.id || "", t.name || "", t.description || "",
      stsFmtTime(t.startTime), stsFmtTime(t.endTime),
      stsFmtDay(t.startTime), stsFmtDay(t.endTime),
      t.beforeStartToleranceMinute != null ? t.beforeStartToleranceMinute : "",
      t.afterStartToleranceMinute != null ? t.afterStartToleranceMinute : "",
      t.lateInToleranceMinute != null ? t.lateInToleranceMinute : "",
      t.earlyOutToleranceMinute != null ? t.earlyOutToleranceMinute : "",
      stsBoolStr(t.report), stsBoolStr(t.monday), stsBoolStr(t.tuesday), stsBoolStr(t.wednesday),
      stsBoolStr(t.thursday), stsBoolStr(t.friday), stsBoolStr(t.saturday), stsBoolStr(t.sunday)
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

  var STS_BASE = function () { return AppState.BASE_URL + "/api/attendance/shift_template_sets"; };
  var ST_REF = function () { return AppState.BASE_URL + "/api/attendance/shift_templates"; };

  if (!document.getElementById("screen-sts")) {
    var main = document.createElement("div");
    main.id = "screen-sts"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📋 Shift Template Set</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">📋</div><div><div class="mh-title">Shift Template Set</div><div class="mh-sub">Create · View · Delete</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="sts-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet · full existing sets · shift templates master</div></div>' +
        '<div class="bf-action-card" id="sts-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Blank set_id = create · filled set_id = update</div></div>' +
        '<div class="bf-action-card" id="sts-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Full detail — one row per shift template entry</div></div>' +
        '<div class="bf-action-card" id="sts-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete sets by comma-separated IDs</div></div>' +
      '</div>';
    modal.appendChild(main);

    var create = document.createElement("div");
    create.id = "screen-sts-create"; create.style.display = "none";
    create.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-sts">📋 Shift Template Set</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>' +
      '<div class="bf-info-box">' +
        'Columns: <b>set_id</b> (blank = create, filled = update) · <b>set_name</b> · <b>set_description</b> · <b>entry_id</b> (shift template id to attach).<br>' +
        'Multiple rows with the same set_id/set_name = multiple shift templates in one set.' +
      '</div>' +
      '<div id="sts-create-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="sts-file"><span id="sts-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="sts-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="sts-c-prog"><div class="bf-pb" id="sts-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="sts-create-log"></div>' +
      '<button class="bf-btn bf-success" id="sts-submit" disabled>🚀 Submit Shift Template Sets</button>' +
      '<button class="bf-btn bf-outline" id="sts-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="sts-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(create);

    var view = document.createElement("div");
    view.id = "screen-sts-view"; view.style.display = "none";
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-sts">📋 Shift Template Set</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>' +
      '<div id="sts-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="sts-v-prog" style="display:none"><div class="bf-pb" id="sts-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="sts-fetch">⬇️ Download Shift Template Sets</button>';
    modal.appendChild(view);

    var del = document.createElement("div");
    del.id = "screen-sts-delete"; del.style.display = "none";
    del.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-sts">📋 Shift Template Set</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>' +
      '<div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>' +
      '<div id="sts-delete-status" class="bf-status"></div>' +
      '<label class="bf-label">Set IDs to delete (comma-separated)</label>' +
      '<input type="text" id="sts-del-ids" placeholder="103, 104" />' +
      '<label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="sts-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>' +
      '<div class="bf-log" id="sts-delete-log"></div>' +
      '<button class="bf-btn bf-danger" id="sts-do-delete" style="margin-top:10px;">🗑️ Delete</button>';
    modal.appendChild(del);

    Router.register("screen-sts", "screen-sts-create", "screen-sts-view", "screen-sts-delete");
    [main, create, view, del].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  function stsFetchAllSets() {
    return ApiTracker.fetch(STS_BASE() + "?projection=FULL", { headers: apiH() }, "Shift Template Set")
      .then(function (r) {
        if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
        return r.json();
      })
      .then(function (raw) { return Array.isArray(raw) ? raw : (raw.content || raw.data || []); });
  }

  document.getElementById("sts-action-tpl").onclick = function () {
    var btn = document.getElementById("sts-action-tpl"); btn.style.opacity = "0.6";
    Promise.all([
      stsFetchAllSets().catch(function () { return []; }),
      ApiTracker.fetch(ST_REF(), { headers: apiH() }, "Shift Template Set").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
    ]).then(function (results) {
      var sets = results[0] || [];
      var templates = results[1] || [];
      var existRows = [];
      sets.forEach(function (s) { stsFlattenSet(s).forEach(function (row) { existRows.push(row); }); });

      downloadExcel("shift_template_sets_template.xlsx", [
        { name: "Upload_Template", tabColor: "D97706", headers: STS_UPLOAD_HEADERS, rows: [], highlightCols: STS_UPLOAD_INPUT_COLS },
        { name: "Existing_Sets_Full", tabColor: "7C3AED", headers: STS_VIEW_HEADERS, rows: existRows },
        { name: "Shift_Templates_Master", tabColor: "059669", headers: ["id", "name", "description"], rows: templates.map(function (t) { return [t.id, t.name || "", t.description || ""]; }) }
      ]);
      btn.style.opacity = "1";
    });
  };

  document.getElementById("sts-action-create").onclick = function () {
    Notifications.clearLog("sts-create-log");
    AppState.cache.sts = null; AppState.cache.stsSuccessRows = []; AppState.cache.stsFailedRows = [];
    document.getElementById("sts-submit").disabled = true;
    document.getElementById("sts-dl-success").style.display = "none";
    document.getElementById("sts-dl-failed").style.display = "none";
    Router.go("screen-sts-create");
  };
  document.getElementById("sts-action-view").onclick = function () { Router.go("screen-sts-view"); };
  document.getElementById("sts-action-delete").onclick = function () { Notifications.clearLog("sts-delete-log"); Router.go("screen-sts-delete"); };

  wireFileInput("sts-file", "sts-file-name", "sts-submit", "sts");

  document.getElementById("sts-dl-success").onclick = function () {
    downloadExcel("sts_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["set_id", "set_name", "entries_submitted", "action"], rows: (AppState.cache.stsSuccessRows || []).map(function (r) { return [r.id || "", r.name, r.entries, r.action]; }) }]);
  };
  document.getElementById("sts-dl-failed").onclick = function () {
    downloadExcel("sts_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["set_name", "http_status", "error"], rows: (AppState.cache.stsFailedRows || []).map(function (r) { return [r.name, r.status || "", r.error || ""]; }) }]);
  };

  document.getElementById("sts-submit").onclick = function () {
    var btn = document.getElementById("sts-submit");
    var rows = AppState.cache.sts || [];
    Notifications.clearLog("sts-create-log");
    document.getElementById("sts-dl-success").style.display = "none";
    document.getElementById("sts-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("sts-create-status", "❌ No data found"); return; }

    function col(row, name) {
      var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
      return k ? String(row[k] || "").trim() : "";
    }

    var updateGroups = {}, createGroups = {}, parseErrors = [];
    rows.forEach(function (row, i) {
      var setId = parseIntSafe(col(row, "set_id"));
      var setName = col(row, "set_name");
      var entryId = parseIntSafe(col(row, "entry_id"));
      if (entryId === null) { parseErrors.push("Row " + (i + 2) + ": entry_id is required/invalid"); return; }
      if (setId !== null) { if (!updateGroups[setId]) updateGroups[setId] = []; updateGroups[setId].push(row); }
      else { if (!setName) { parseErrors.push("Row " + (i + 2) + ": set_name required when set_id is blank"); return; } if (!createGroups[setName]) createGroups[setName] = []; createGroups[setName].push(row); }
    });
    if (parseErrors.length) parseErrors.forEach(function (e) { Notifications.log("sts-create-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });

    var updateEntries = Object.keys(updateGroups).map(function (k) { return [k, updateGroups[k]]; });
    var createEntries = Object.keys(createGroups).map(function (k) { return [k, createGroups[k]]; });
    var total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error("sts-create-status", "❌ No valid groups found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("sts-c-prog");
    AppState.cache.stsSuccessRows = []; AppState.cache.stsFailedRows = [];
    var s = 0, f = 0, done = 0;

    function buildEntries(group) {
      var entries = [], seen = {};
      group.forEach(function (row) {
        var entryId = parseIntSafe(col(row, "entry_id"));
        if (entryId === null || seen[entryId]) return;
        seen[entryId] = true;
        entries.push({ id: entryId });
      });
      return entries;
    }

    function processUpdate(i) {
      if (i >= updateEntries.length) return processCreate(0);
      var setId = updateEntries[i][0], group = updateEntries[i][1], first = group[0];
      var payload = { id: parseInt(setId), name: col(first, "set_name"), description: col(first, "set_description") || col(first, "set_name"), entries: buildEntries(group) };
      ApiTracker.fetch(STS_BASE() + "/" + payload.id + "/", { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Shift Template Set").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            Notifications.log("sts-create-log", "✅ Updated: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("updated", 1);
            AppState.cache.stsSuccessRows.push({ id: payload.id, name: payload.name, entries: payload.entries.length, action: "Updated" });
          } else {
            var err = parseApiError(body);
            Notifications.log("sts-create-log", "❌ Failed update: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.stsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("sts-create-log", "❌ Error: " + payload.name + " — " + e.message, "fail");
        f++; AppState.cache.stsFailedRows.push({ name: payload.name, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("sts-c-bar", (done / total) * 100);
        processUpdate(i + 1);
      });
    }

    function processCreate(i) {
      if (i >= createEntries.length) return finish();
      var setName = createEntries[i][0], group = createEntries[i][1], first = group[0];
      var payload = { name: setName, description: col(first, "set_description") || setName, entries: buildEntries(group) };
      ApiTracker.fetch(STS_BASE() + "/", { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Shift Template Set").then(function (r) {
        return r.text().then(function (body) {
          var createdId = ""; try { createdId = JSON.parse(body).id || ""; } catch (e) {}
          if (r.ok) {
            Notifications.log("sts-create-log", "✅ Created: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("created", 1);
            AppState.cache.stsSuccessRows.push({ id: createdId, name: payload.name, entries: payload.entries.length, action: "Created" });
          } else {
            var err = parseApiError(body);
            Notifications.log("sts-create-log", "❌ Failed create: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.stsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("sts-create-log", "❌ Error: " + e.message, "fail");
        f++; AppState.cache.stsFailedRows.push({ name: setName, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("sts-c-bar", (done / total) * 100);
        processCreate(i + 1);
      });
    }

    function finish() {
      Notifications.log("sts-create-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("sts-create-log", "✅ Success: " + s + "  ❌ Failed: " + f, f === 0 ? "ok" : "info");
      Notifications.status("sts-create-status", "Done — " + s + " success, " + f + " failed", f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Submit Shift Template Sets");
      Notifications.progress.hide("sts-c-prog");
      if (AppState.cache.stsSuccessRows.length) document.getElementById("sts-dl-success").style.display = "block";
      if (AppState.cache.stsFailedRows.length) document.getElementById("sts-dl-failed").style.display = "block";
    }

    processUpdate(0);
  };

  document.getElementById("sts-fetch").onclick = function () {
    var btn = document.getElementById("sts-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("sts-v-prog");
    Notifications.info("sts-view-status", "⏳ Fetching shift template sets (FULL projection)..."); Notifications.progress.set("sts-v-bar", 20);
    stsFetchAllSets().then(function (sets) {
      if (!sets.length) { Notifications.info("sts-view-status", "ℹ️ No sets found."); return; }
      Notifications.info("sts-view-status", "⏳ Processing " + sets.length + " set(s)..."); Notifications.progress.set("sts-v-bar", 60);
      var rows = [];
      sets.forEach(function (s) { stsFlattenSet(s).forEach(function (row) { rows.push(row); }); });
      Notifications.info("sts-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("sts-v-bar", 90);
      downloadExcel("shift_template_sets_" + new Date().toISOString().slice(0, 10) + ".xlsx", [{ name: "Shift_Template_Sets", tabColor: "D97706", headers: STS_VIEW_HEADERS, rows: rows }]);
      Notifications.progress.set("sts-v-bar", 100);
      Notifications.success("sts-view-status", "✅ Download complete — " + sets.length + " set(s), " + rows.length + " row(s)");
    }).catch(function (e) {
      Notifications.error("sts-view-status", "❌ " + e.message); Notifications.progress.set("sts-v-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "⬇️ Download Shift Template Sets");
      Notifications.progress.hide("sts-v-prog", 2000);
    });
  };

  document.getElementById("sts-do-delete").onclick = function () {
    if (!document.getElementById("sts-confirm").checked) { Notifications.error("sts-delete-status", "⚠️ Check confirmation box"); return; }
    var ids = document.getElementById("sts-del-ids").value.split(",").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    if (!ids.length) { Notifications.error("sts-delete-status", "❌ No IDs entered"); return; }
    var btn = document.getElementById("sts-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("sts-delete-log");
    var s = 0, f = 0;
    function next(i) {
      if (i >= ids.length) {
        Audit.onDbOp("deleted", s);
        Notifications.status("sts-delete-status", "Done — " + s + " deleted, " + f + " failed", f === 0 ? "success" : "info");
        Notifications.doneLoading(btn, "🗑️ Delete");
        return;
      }
      var id = ids[i];
      ApiTracker.fetch(STS_BASE() + "/" + id, { method: "DELETE", headers: apiH() }, "Shift Template Set").then(function (r) {
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("sts-delete-log", "✅ Deleted: " + id, "ok"); s++; next(i + 1); }
        else return r.text().then(function (t) { Notifications.log("sts-delete-log", "❌ Failed: " + id + " — " + parseApiError(t), "fail"); f++; next(i + 1); });
      }).catch(function (e) { Notifications.log("sts-delete-log", "❌ Error: " + id + " — " + e.message, "fail"); f++; next(i + 1); });
    }
    next(0);
  };

  console.log("✅ Shift Template Set module loaded — full detail view · simplified 4-col upload");
}