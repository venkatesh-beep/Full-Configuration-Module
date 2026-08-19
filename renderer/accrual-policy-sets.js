/* =========================================================
 * accrual-policy-sets.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-aps, screen-aps-create, screen-aps-view, screen-aps-delete
 * GET    /api/attendance/accrual_policy_sets?projection=FULL
 * POST   /api/attendance/accrual_policy_sets            (create)
 * PUT    /api/attendance/accrual_policy_sets/{id}        (update)
 * DELETE /api/attendance/accrual_policy_sets/{id}
 *
 * Upload columns (Sheet 1): ID, Accrual Set Name, Accrual Set Description,
 * Accrual Policy ID
 *   - Accrual Policy ID is the accrual_policy id to attach to this set.
 *   - blank ID  -> creates a new set (POST)
 *   - filled ID -> updates the existing set (PUT), replacing its entries
 *                  with whatever rows were uploaded for it
 *
 * View / "Existing Sets" format (Sheet 2 of the template, and the
 * View Existing download) — one row per (set, entry), flattened with
 * the accrual policy's own fields:
 *   id, Accrual Set Name, Accrual Set Description,
 *   id, Accrual Policy Name, Accrual Policy Description, Accrual ID
 * ========================================================= */

var APS_VIEW_HEADERS = [
  "id", "Accrual Set Name", "Accrual Set Description",
  "id", "Accrual Policy Name", "Accrual Policy Description", "Accrual ID"
];
var APS_UPLOAD_HEADERS = ["ID", "Accrual Set Name", "Accrual Set Description", "Accrual Policy ID"];
var APS_UPLOAD_INPUT_COLS = [1, 3]; // Accrual Set Name, Accrual Policy ID

/** Flattens ONE set (with its FULL-projection accrualPolicy entries) into
 *  one row per entry, matching APS_VIEW_HEADERS exactly. */
function apsFlattenSet(set) {
  var rows = [];
  var entries = set.entries || [];
  if (!entries.length) {
    rows.push([set.id, set.name || "", set.description || "", "", "", "", ""]);
    return rows;
  }
  entries.forEach(function (entry) {
    // API entries are flat (matching how they're written: {"id": N}) — the
    // FULL projection expands this straight into the policy's own fields,
    // it is NOT wrapped under an "accrualPolicy" key. Fall back to entry
    // itself if a wrapper isn't present, so this works either way.
    var p = entry.accrualPolicy || entry || {};
    var accrualId = (p.accrual && p.accrual.id != null) ? p.accrual.id : "";
    rows.push([
      set.id, set.name || "", set.description || "",
      p.id || "", p.name || "", p.description || "",
      accrualId
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

  var APS_BASE = function () { return AppState.BASE_URL + "/api/attendance/accrual_policy_sets"; };
  var APOL_REF = function () { return AppState.BASE_URL + "/api/attendance/accrual_policies"; };

  if (!document.getElementById("screen-aps")) {
    var main = document.createElement("div");
    main.id = "screen-aps"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📑 Accrual Policy Set</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">📑</div><div><div class="mh-title">Accrual Policy Set</div><div class="mh-sub">Create · View · Delete</div></div></div>' +
      '<div class="bf-action-grid">' +
        '<div class="bf-action-card" id="aps-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Upload sheet · full existing sets · accrual policies master</div></div>' +
        '<div class="bf-action-card" id="aps-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Blank ID = create · filled ID = update</div></div>' +
        '<div class="bf-action-card" id="aps-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Full detail — one row per accrual policy entry</div></div>' +
        '<div class="bf-action-card" id="aps-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete sets by comma-separated IDs</div></div>' +
      '</div>';
    modal.appendChild(main);

    var create = document.createElement("div");
    create.id = "screen-aps-create"; create.style.display = "none";
    create.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-aps">📑 Accrual Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>' +
      '<div class="bf-info-box">' +
        'Columns: <b>ID</b> (blank = create, filled = update) · <b>Accrual Set Name</b> · <b>Accrual Set Description</b> · <b>Accrual Policy ID</b> (policy id to attach).<br>' +
        'Multiple rows with the same ID/Accrual Set Name = multiple accrual policies in one set.' +
      '</div>' +
      '<div id="aps-create-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="aps-file"><span id="aps-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="aps-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="aps-c-prog"><div class="bf-pb" id="aps-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="aps-create-log"></div>' +
      '<button class="bf-btn bf-success" id="aps-submit" disabled>🚀 Submit Accrual Policy Sets</button>' +
      '<button class="bf-btn bf-outline" id="aps-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="aps-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(create);

    var view = document.createElement("div");
    view.id = "screen-aps-view"; view.style.display = "none";
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-aps">📑 Accrual Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>' +
      '<div id="aps-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="aps-v-prog" style="display:none"><div class="bf-pb" id="aps-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="aps-fetch">⬇️ Download Accrual Policy Sets</button>';
    modal.appendChild(view);

    var del = document.createElement("div");
    del.id = "screen-aps-delete"; del.style.display = "none";
    del.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-aps">📑 Accrual Policy Set</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>' +
      '<div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>' +
      '<div id="aps-delete-status" class="bf-status"></div>' +
      '<label class="bf-label">Set IDs to delete (comma-separated)</label>' +
      '<input type="text" id="aps-del-ids" placeholder="39, 40" />' +
      '<label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="aps-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>' +
      '<div class="bf-log" id="aps-delete-log"></div>' +
      '<button class="bf-btn bf-danger" id="aps-do-delete" style="margin-top:10px;">🗑️ Delete</button>';
    modal.appendChild(del);

    Router.register("screen-aps", "screen-aps-create", "screen-aps-view", "screen-aps-delete");
    [main, create, view, del].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  function apsFetchAllSets() {
    return ApiTracker.fetch(APS_BASE() + "/?projection=FULL", { headers: apiH() }, "Accrual Policy Set")
      .then(function (r) {
        if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
        return r.json();
      })
      .then(function (raw) { return Array.isArray(raw) ? raw : (raw.content || raw.data || []); });
  }

  document.getElementById("aps-action-tpl").onclick = function () {
    var btn = document.getElementById("aps-action-tpl"); btn.style.opacity = "0.6";
    Promise.all([
      apsFetchAllSets().catch(function () { return []; }),
      ApiTracker.fetch(APOL_REF(), { headers: apiH() }, "Accrual Policy Set").then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; })
    ]).then(function (results) {
      var sets = results[0] || [];
      var rawPolicies = results[1] || [];
      var policies = Array.isArray(rawPolicies) ? rawPolicies : (rawPolicies.content || []);
      var existRows = [];
      sets.forEach(function (s) { apsFlattenSet(s).forEach(function (row) { existRows.push(row); }); });

      downloadExcel("accrual_policy_sets_template.xlsx", [
        { name: "Upload_Template", tabColor: "0369A1", headers: APS_UPLOAD_HEADERS, rows: [], highlightCols: APS_UPLOAD_INPUT_COLS },
        { name: "Existing_Sets_Full", tabColor: "7C3AED", headers: APS_VIEW_HEADERS, rows: existRows },
        { name: "Accrual_Policies_Master", tabColor: "059669", headers: ["id", "name", "description"], rows: policies.map(function (p) { return [p.id, p.name || "", p.description || ""]; }) }
      ]);
      btn.style.opacity = "1";
    });
  };

  document.getElementById("aps-action-create").onclick = function () {
    Notifications.clearLog("aps-create-log");
    AppState.cache.aps = null; AppState.cache.apsSuccessRows = []; AppState.cache.apsFailedRows = [];
    document.getElementById("aps-submit").disabled = true;
    document.getElementById("aps-dl-success").style.display = "none";
    document.getElementById("aps-dl-failed").style.display = "none";
    Router.go("screen-aps-create");
  };
  document.getElementById("aps-action-view").onclick = function () { Router.go("screen-aps-view"); };
  document.getElementById("aps-action-delete").onclick = function () { Notifications.clearLog("aps-delete-log"); Router.go("screen-aps-delete"); };

  wireFileInput("aps-file", "aps-file-name", "aps-submit", "aps");

  document.getElementById("aps-dl-success").onclick = function () {
    downloadExcel("aps_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["set_id", "set_name", "entries_submitted", "action"], rows: (AppState.cache.apsSuccessRows || []).map(function (r) { return [r.id || "", r.name, r.entries, r.action]; }) }]);
  };
  document.getElementById("aps-dl-failed").onclick = function () {
    downloadExcel("aps_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["set_name", "http_status", "error"], rows: (AppState.cache.apsFailedRows || []).map(function (r) { return [r.name, r.status || "", r.error || ""]; }) }]);
  };

  document.getElementById("aps-submit").onclick = function () {
    var btn = document.getElementById("aps-submit");
    var rows = AppState.cache.aps || [];
    Notifications.clearLog("aps-create-log");
    document.getElementById("aps-dl-success").style.display = "none";
    document.getElementById("aps-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("aps-create-status", "❌ No data found"); return; }

    function col(row, name) {
      var k = Object.keys(row).filter(function (k) { return k.trim().toLowerCase() === name.toLowerCase(); })[0];
      return k ? String(row[k] || "").trim() : "";
    }

    var updateGroups = {}, createGroups = {}, parseErrors = [];
    rows.forEach(function (row, i) {
      var setId = parseIntSafe(col(row, "ID"));
      var setName = col(row, "Accrual Set Name");
      var policyId = parseIntSafe(col(row, "Accrual Policy ID"));
      if (policyId === null) { parseErrors.push("Row " + (i + 2) + ": Accrual Policy ID is required/invalid"); return; }
      if (setId !== null) { if (!updateGroups[setId]) updateGroups[setId] = []; updateGroups[setId].push(row); }
      else { if (!setName) { parseErrors.push("Row " + (i + 2) + ": Accrual Set Name required when ID is blank"); return; } if (!createGroups[setName]) createGroups[setName] = []; createGroups[setName].push(row); }
    });
    if (parseErrors.length) parseErrors.forEach(function (e) { Notifications.log("aps-create-log", "⚠️ " + e, "fail"); Audit.onValidationError(e); });

    var updateEntries = Object.keys(updateGroups).map(function (k) { return [k, updateGroups[k]]; });
    var createEntries = Object.keys(createGroups).map(function (k) { return [k, createGroups[k]]; });
    var total = updateEntries.length + createEntries.length;
    if (!total) { Notifications.error("aps-create-status", "❌ No valid groups found"); return; }

    Notifications.loading(btn, "Submitting...");
    Notifications.progress.show("aps-c-prog");
    AppState.cache.apsSuccessRows = []; AppState.cache.apsFailedRows = [];
    var s = 0, f = 0, done = 0;

    function buildEntries(group) {
      var entries = [], seen = {};
      group.forEach(function (row) {
        var policyId = parseIntSafe(col(row, "Accrual Policy ID"));
        if (policyId === null || seen[policyId]) return;
        seen[policyId] = true;
        entries.push({ id: policyId });
      });
      return entries;
    }

    function processUpdate(i) {
      if (i >= updateEntries.length) return processCreate(0);
      var setId = updateEntries[i][0], group = updateEntries[i][1], first = group[0];
      var payload = { id: parseInt(setId), name: col(first, "Accrual Set Name"), description: col(first, "Accrual Set Description") || col(first, "Accrual Set Name"), entries: buildEntries(group) };
      ApiTracker.fetch(APS_BASE() + "/" + payload.id, { method: "PUT", headers: apiH(), body: JSON.stringify(payload) }, "Accrual Policy Set").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            Notifications.log("aps-create-log", "✅ Updated: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("updated", 1);
            AppState.cache.apsSuccessRows.push({ id: payload.id, name: payload.name, entries: payload.entries.length, action: "Updated" });
          } else {
            var err = parseApiError(body);
            Notifications.log("aps-create-log", "❌ Failed update: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.apsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("aps-create-log", "❌ Error: " + payload.name + " — " + e.message, "fail");
        f++; AppState.cache.apsFailedRows.push({ name: payload.name, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("aps-c-bar", (done / total) * 100);
        processUpdate(i + 1);
      });
    }

    function processCreate(i) {
      if (i >= createEntries.length) return finish();
      var setName = createEntries[i][0], group = createEntries[i][1], first = group[0];
      var payload = { name: setName, description: col(first, "Accrual Set Description") || setName, entries: buildEntries(group) };
      ApiTracker.fetch(APS_BASE(), { method: "POST", headers: apiH(), body: JSON.stringify(payload) }, "Accrual Policy Set").then(function (r) {
        return r.text().then(function (body) {
          var createdId = ""; try { createdId = JSON.parse(body).id || ""; } catch (e) {}
          if (r.ok) {
            Notifications.log("aps-create-log", "✅ Created: " + payload.name + " (" + payload.entries.length + " entries)", "ok");
            s++; Audit.onDbOp("created", 1);
            AppState.cache.apsSuccessRows.push({ id: createdId, name: payload.name, entries: payload.entries.length, action: "Created" });
          } else {
            var err = parseApiError(body);
            Notifications.log("aps-create-log", "❌ Failed create: " + payload.name + " — " + err, "fail");
            f++; AppState.cache.apsFailedRows.push({ name: payload.name, status: r.status, error: err });
          }
        });
      }).catch(function (e) {
        Notifications.log("aps-create-log", "❌ Error: " + e.message, "fail");
        f++; AppState.cache.apsFailedRows.push({ name: setName, status: "NET", error: e.message });
      }).then(function () {
        done++; Notifications.progress.set("aps-c-bar", (done / total) * 100);
        processCreate(i + 1);
      });
    }

    function finish() {
      Notifications.log("aps-create-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("aps-create-log", "✅ Success: " + s + "  ❌ Failed: " + f, f === 0 ? "ok" : "info");
      Notifications.status("aps-create-status", "Done — " + s + " success, " + f + " failed", f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Submit Accrual Policy Sets");
      Notifications.progress.hide("aps-c-prog");
      if (AppState.cache.apsSuccessRows.length) document.getElementById("aps-dl-success").style.display = "block";
      if (AppState.cache.apsFailedRows.length) document.getElementById("aps-dl-failed").style.display = "block";
    }

    processUpdate(0);
  };

  document.getElementById("aps-fetch").onclick = function () {
    var btn = document.getElementById("aps-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("aps-v-prog");
    Notifications.info("aps-view-status", "⏳ Fetching accrual policy sets (FULL projection)..."); Notifications.progress.set("aps-v-bar", 20);
    apsFetchAllSets().then(function (sets) {
      if (!sets.length) { Notifications.info("aps-view-status", "ℹ️ No sets found."); return; }
      Notifications.info("aps-view-status", "⏳ Processing " + sets.length + " set(s)..."); Notifications.progress.set("aps-v-bar", 60);
      var rows = [];
      sets.forEach(function (s) { apsFlattenSet(s).forEach(function (row) { rows.push(row); }); });
      Notifications.info("aps-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("aps-v-bar", 90);
      downloadExcel("accrual_policy_sets_" + new Date().toISOString().slice(0, 10) + ".xlsx", [{ name: "Accrual_Policy_Sets", tabColor: "0369A1", headers: APS_VIEW_HEADERS, rows: rows }]);
      Notifications.progress.set("aps-v-bar", 100);
      Notifications.success("aps-view-status", "✅ Download complete — " + sets.length + " set(s), " + rows.length + " row(s)");
    }).catch(function (e) {
      Notifications.error("aps-view-status", "❌ " + e.message); Notifications.progress.set("aps-v-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "⬇️ Download Accrual Policy Sets");
      Notifications.progress.hide("aps-v-prog", 2000);
    });
  };

  document.getElementById("aps-do-delete").onclick = function () {
    if (!document.getElementById("aps-confirm").checked) { Notifications.error("aps-delete-status", "⚠️ Check confirmation box"); return; }
    var ids = document.getElementById("aps-del-ids").value.split(",").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
    if (!ids.length) { Notifications.error("aps-delete-status", "❌ No IDs entered"); return; }
    var btn = document.getElementById("aps-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("aps-delete-log");
    var s = 0, f = 0;
    function next(i) {
      if (i >= ids.length) {
        Audit.onDbOp("deleted", s);
        Notifications.status("aps-delete-status", "Done — " + s + " deleted, " + f + " failed", f === 0 ? "success" : "info");
        Notifications.doneLoading(btn, "🗑️ Delete");
        return;
      }
      var id = ids[i];
      ApiTracker.fetch(APS_BASE() + "/" + id, { method: "DELETE", headers: apiH() }, "Accrual Policy Set").then(function (r) {
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("aps-delete-log", "✅ Deleted: " + id, "ok"); s++; next(i + 1); }
        else return r.text().then(function (t) { Notifications.log("aps-delete-log", "❌ Failed: " + id + " — " + parseApiError(t), "fail"); f++; next(i + 1); });
      }).catch(function (e) { Notifications.log("aps-delete-log", "❌ Error: " + id + " — " + e.message, "fail"); f++; next(i + 1); });
    }
    next(0);
  };

  console.log("✅ Accrual Policy Set module loaded — full detail view · simplified 4-col upload");
}