/* =========================================================
 * roles.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-rol, screen-rol-upload, screen-rol-view
 * Requires a SUPERADMIN-level BeeForce login. Base URL differs from
 * every other module: /api/data-management/api/*
 *
 * CONFIRMED against real curl examples:
 *   - "Connecting to a tenant" is NOT a separate token exchange — it is
 *     simply adding an `x-organization-id: <id>` header to your normal
 *     Bearer token on every data-management request from then on.
 *   - GET  /api/data-management/api/organization-masters/position
 *          headers: Authorization, x-organization-id, Accept
 *   - POST /api/data-management/api/organization-masters/position
 *          (SAME URL for both create AND update — no id in the path.
 *           Presence of "id" in the JSON body is what makes it an update.)
 * ========================================================= */

var ROL_POS_HEADERS = [
  "id (blank=create)", "positionName", "activeStatus", "personType_id", "personType_description",
  "locationAccess", "positionAccessRequired", "positionRequiredForDelegation", "roles (comma-separated)"
];
var ROL_POS_INPUT = [1, 2, 3, 4];
var ROL_VIEW_HEADERS = ["id", "personType_description", "personType_id", "positionAccessRequired", "positionName", "positionRequiredForDelegation", "role_id"];

function rolFlatPos(pos) {
  var rows = [];
  var base = [
    pos.id || "", (pos.personType && pos.personType.description) || "", (pos.personType && pos.personType.id) || "",
    pos.positionAccessRequired ? "TRUE" : "FALSE", pos.positionName || "",
    pos.positionRequiredForDelegation ? "TRUE" : "FALSE"
  ];
  var roles = pos.roles || [];
  if (!roles.length) { rows.push(base.concat([""])); return rows; }
  roles.forEach(function (r) { rows.push(base.concat([r])); });
  return rows;
}
function rolPersonType(id, desc) {
  return {
    createUser: null, created: null,
    description: desc || (parseInt(id) === 2 ? "Contractor" : "Employee"),
    id: parseInt(id) || 1,
    lastUpdateUser: null, lastUpdated: null, personType: null
  };
}

/** Robust search-box matcher: builds one lowercase string out of EVERY
 *  string/number value in the tenant object (not just a couple of
 *  guessed field names), so filtering works regardless of exactly
 *  which fields the tenant list API actually returns. */
function rolTenantSearchText(t) {
  var parts = [];
  Object.keys(t || {}).forEach(function (k) {
    var v = t[k];
    if (typeof v === "string" || typeof v === "number") parts.push(String(v));
  });
  return parts.join(" ").toLowerCase();
}
function rolTenantLabel(t) {
  return t.detailedDescription || t.name || t.organizationName || t.orgName || t.description || ("Org " + t.id);
}

function init(ctx) {
  var AppState = ctx.AppState;
  var downloadExcel = ctx.downloadExcel;
  var wireFileInput = ctx.wireFileInput;
  var parseApiError = ctx.parseApiError;
  var parseIntSafe = ctx.parseIntSafe;
  var Notifications = ctx.Notifications;
  var Router = ctx.Router;
  var Audit = ctx.Audit;
  var ApiTracker = ctx.ApiTracker;
  var modal = ctx.modal;

  var ROL_DM = function () { return AppState.BASE_URL + "/api/data-management/api"; };

  /** Same as the normal apiH() everywhere else, PLUS the selected
   *  tenant's x-organization-id once one has been chosen. This is the
   *  entire "connect to tenant" mechanism — no separate token needed. */
  function rolH() {
    var h = {
      "Authorization": "Bearer " + AppState.TOKEN,
      "Content-Type": "application/json",
      "Accept": "application/json"
    };
    if (AppState.cache.rolSelectedOrgId) h["x-organization-id"] = String(AppState.cache.rolSelectedOrgId);
    return h;
  }

  if (!document.getElementById("screen-rol")) {
    var main = document.createElement("div");
    main.id = "screen-rol"; main.style.display = "none";
    main.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">🔑 Roles & Positions</span></div>' +
      '<div class="bf-module-header"><div class="mh-icon">🔑</div><div><div class="mh-title">Roles & Positions</div><div class="mh-sub">SUPERADMIN · Select Tenant · Upload / View Positions</div></div></div>' +

      '<div style="background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:10px;padding:12px 16px;margin-bottom:14px;">' +
        '<div style="font-weight:700;color:#92400E;margin-bottom:4px;">⚠️ SUPERADMIN Access Required</div>' +
        '<div style="font-size:12px;color:#78350F;">This module uses the Data Management API and requires a SUPERADMIN-level BeeForce login. The standard tenant login will NOT work here.</div>' +
      '</div>' +

      '<div class="bf-section-label">Step 1 — Load tenant list</div>' +
      '<button class="bf-btn bf-outline" id="rol-load-tenants" style="margin-bottom:12px">🔄 Load Tenants</button>' +
      '<div id="rol-tenant-status" class="bf-status"></div>' +

      '<div id="rol-tenant-section" style="display:none">' +
        '<div class="bf-section-label">Step 2 — Select tenant</div>' +
        '<input type="text" id="rol-tenant-search" placeholder="🔍 Search tenant name..." style="margin-bottom:8px" />' +
        '<div id="rol-tenant-list" style="max-height:200px;overflow-y:auto;border:1.5px solid #E5E7EB;border-radius:8px;background:#fff;margin-bottom:12px;"></div>' +
        '<div id="rol-selected-org" style="display:none;padding:10px 14px;background:#EFF6FF;border:1.5px solid #BFDBFE;border-radius:8px;margin-bottom:12px;font-size:13px;">' +
          'Selected: <b id="rol-org-name"></b> (ID: <span id="rol-org-id"></span>)' +
        '</div>' +
        '<button class="bf-btn bf-primary" id="rol-connect" style="display:none">🔗 Connect to Tenant</button>' +
      '</div>' +

      '<div id="rol-action-section" style="display:none">' +
        '<div id="rol-connected-banner" style="padding:10px 14px;background:#D1FAE5;border:1.5px solid #6EE7B7;border-radius:8px;margin-bottom:14px;font-size:13px;">' +
          '✅ Connected to: <b id="rol-connected-name"></b>' +
        '</div>' +
        '<div class="bf-section-label">Step 3 — Actions</div>' +
        '<div class="bf-action-grid">' +
          '<div class="bf-action-card" id="rol-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">Sheet 1: upload · Sheet 2: roles · Sheet 3: existing positions</div></div>' +
          '<div class="bf-action-card" id="rol-action-upload"><div class="ac-icon">📤</div><div class="ac-name">Upload Positions</div><div class="ac-desc">id blank=create · id filled=update · roles comma-separated</div></div>' +
          '<div class="bf-action-card" id="rol-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Positions</div><div class="ac-desc">Fetch all positions individually and download as Excel</div></div>' +
        '</div>' +
      '</div>';
    modal.appendChild(main);

    var upload = document.createElement("div");
    upload.id = "screen-rol-upload"; upload.style.display = "none";
    upload.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-rol">🔑 Roles & Positions</span><span class="bc-sep">›</span><span class="bc-cur">Upload Positions</span></div>' +
      '<div class="bf-info-box">' +
        '<b>Columns:</b> id (blank=create), positionName, activeStatus, personType_id, personType_description, locationAccess, positionAccessRequired, positionRequiredForDelegation, roles (comma-separated role IDs).<br>' +
        'Multiple rows with the same positionName are merged — roles collected from all rows.' +
      '</div>' +
      '<div id="rol-upload-status" class="bf-status"></div>' +
      '<label class="bf-file-label" for="rol-file"><span id="rol-file-name">📂 Click to select filled template (.xlsx)</span></label>' +
      '<input type="file" id="rol-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />' +
      '<div class="bf-progress" id="rol-c-prog"><div class="bf-pb" id="rol-c-bar" style="width:0%"></div></div>' +
      '<div class="bf-log" id="rol-upload-log"></div>' +
      '<button class="bf-btn bf-success" id="rol-submit" disabled>🚀 Create / Update Positions</button>' +
      '<button class="bf-btn bf-outline" id="rol-dl-success" style="display:none">⬇️ Download Success Report</button>' +
      '<button class="bf-btn bf-outline" id="rol-dl-failed"  style="display:none">⬇️ Download Failed Report</button>';
    modal.appendChild(upload);

    var view = document.createElement("div");
    view.id = "screen-rol-view"; view.style.display = "none";
    view.innerHTML =
      '<div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-rol">🔑 Roles & Positions</span><span class="bc-sep">›</span><span class="bc-cur">View Positions</span></div>' +
      '<div id="rol-view-status" class="bf-status"></div>' +
      '<div class="bf-progress" id="rol-v-prog" style="display:none"><div class="bf-pb" id="rol-v-bar" style="width:0%"></div></div>' +
      '<button class="bf-btn bf-primary" id="rol-fetch">⬇️ Download All Positions</button>';
    modal.appendChild(view);

    Router.register("screen-rol", "screen-rol-upload", "screen-rol-view");
    [main, upload, view].forEach(function (el) {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(function (inp) {
        ["keydown", "keyup", "keypress", "input"].forEach(function (evt) {
          inp.addEventListener(evt, function (e) { e.stopPropagation(); }, true);
        });
      });
    });
  }

  // ── Load Tenants ──────────────────────────────────────────
  document.getElementById("rol-load-tenants").onclick = function () {
    var btn = document.getElementById("rol-load-tenants");
    Notifications.loading(btn, "Loading...");
    Notifications.info("rol-tenant-status", "⏳ Fetching tenant list...");
    ApiTracker.fetch(ROL_DM() + "/master/getAll", { headers: rolH() }, "Roles & Positions").then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
      return r.json();
    }).then(function (raw) {
      var list = Array.isArray(raw) ? raw : (raw.data || raw.result || raw.organizations || raw.content || []);
      if (!list.length) throw new Error("No tenants returned");

      AppState.cache.rolTenants = list;
      renderTenantList(list, "");
      document.getElementById("rol-tenant-section").style.display = "block";
      Notifications.success("rol-tenant-status", "✅ " + list.length + " tenant(s) loaded");

      document.getElementById("rol-tenant-search").oninput = function (e) {
        renderTenantList(AppState.cache.rolTenants, e.target.value.toLowerCase().trim());
      };
    }).catch(function (e) {
      Notifications.error("rol-tenant-status", "❌ " + e.message);
    }).then(function () {
      Notifications.doneLoading(btn, "🔄 Load Tenants");
    });
  };

  function renderTenantList(tenants, filter) {
    var listEl = document.getElementById("rol-tenant-list");
    var filtered = tenants.filter(function (t) {
      return !filter || rolTenantSearchText(t).indexOf(filter) !== -1;
    });
    listEl.innerHTML = filtered.map(function (t) {
      var label = rolTenantLabel(t);
      return '<div class="rol-tenant-row" data-id="' + t.id + '" data-name="' + label.replace(/"/g, "&quot;") + '" ' +
        'style="padding:9px 14px;cursor:pointer;border-bottom:1px solid #F3F4F6;font-size:13px;transition:background 0.15s;">' +
        '<span style="font-weight:600;color:#1D4ED8">' + label + '</span>' +
        '<span style="color:#9CA3AF;font-size:11px;margin-left:8px">ID: ' + t.id + '</span>' +
      '</div>';
    }).join("") || '<div style="padding:12px;color:#9CA3AF;text-align:center">No results</div>';

    listEl.querySelectorAll(".rol-tenant-row").forEach(function (row) {
      row.addEventListener("mouseover", function () { if (row.dataset.id != AppState.cache.rolSelectedOrgId) row.style.background = "#F9FAFB"; });
      row.addEventListener("mouseout", function () { if (row.dataset.id != AppState.cache.rolSelectedOrgId) row.style.background = ""; });
      row.addEventListener("click", function () { selectRolTenant(row.dataset.id, row.dataset.name); });
    });
  }

  function selectRolTenant(id, name) {
    AppState.cache.rolSelectedOrgId = id;
    AppState.cache.rolSelectedOrgName = name;
    document.getElementById("rol-org-id").textContent = id;
    document.getElementById("rol-org-name").textContent = name;
    document.getElementById("rol-selected-org").style.display = "block";
    document.getElementById("rol-connect").style.display = "block";
    document.querySelectorAll(".rol-tenant-row").forEach(function (r) {
      r.style.background = r.dataset.id == id ? "#EFF6FF" : "";
      r.style.fontWeight = r.dataset.id == id ? "700" : "";
    });
  }

  // ── Connect to Tenant — just validates the x-organization-id header
  // works by making one real GET call with it. No separate token. ──
  document.getElementById("rol-connect").onclick = function () {
    var btn = document.getElementById("rol-connect");
    var orgId = AppState.cache.rolSelectedOrgId;
    if (!orgId) { Notifications.error("rol-tenant-status", "❌ Select a tenant first"); return; }

    Notifications.loading(btn, "Connecting...");
    Notifications.info("rol-tenant-status", "⏳ Verifying access to this tenant...");
    ApiTracker.fetch(ROL_DM() + "/organization-masters/position", { headers: rolH() }, "Roles & Positions").then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
      document.getElementById("rol-connected-name").textContent = AppState.cache.rolSelectedOrgName;
      document.getElementById("rol-action-section").style.display = "block";
      Notifications.success("rol-tenant-status", "✅ Connected to " + AppState.cache.rolSelectedOrgName);
    }).catch(function (e) {
      Notifications.error("rol-tenant-status", "❌ " + e.message);
    }).then(function () {
      Notifications.doneLoading(btn, "🔗 Connect to Tenant");
    });
  };

  document.getElementById("rol-action-tpl").onclick = function () { rolDownloadTemplate(); };
  document.getElementById("rol-action-upload").onclick = function () {
    Notifications.clearLog("rol-upload-log");
    AppState.cache.rol = null; AppState.cache.rolSuccess = []; AppState.cache.rolFailed = [];
    document.getElementById("rol-submit").disabled = true;
    document.getElementById("rol-dl-success").style.display = "none";
    document.getElementById("rol-dl-failed").style.display = "none";
    Router.go("screen-rol-upload");
  };
  document.getElementById("rol-action-view").onclick = function () { Router.go("screen-rol-view"); };

  function rolFetchPositions(ids) {
    if (!ids.length) return Promise.resolve([]);
    var CONCURRENCY = 10, results = [];
    function nextBatch(i) {
      if (i >= ids.length) return results;
      var batch = ids.slice(i, i + CONCURRENCY);
      var settled = batch.map(function (id) {
        return ApiTracker.fetch(ROL_DM() + "/organization-masters/position/" + id, { headers: rolH() }, "Roles & Positions")
          .then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
      });
      return Promise.all(settled.map(function (p) { return p.then(function (v) { return { ok: true, v: v }; }, function () { return { ok: false, v: null }; }); })).then(function (arr) {
        arr.forEach(function (r) { var pos = r.ok ? (r.v && (r.v.data || r.v)) : null; if (pos && pos.id) results.push(pos); });
        return nextBatch(i + CONCURRENCY);
      });
    }
    return nextBatch(0);
  }

  function rolDownloadTemplate() {
    var btn = document.getElementById("rol-action-tpl"); btn.style.opacity = "0.6";
    var orgId = AppState.cache.rolSelectedOrgId;
    if (!orgId) { Notifications.alert("Please connect to a tenant first."); btn.style.opacity = "1"; return; }
    Notifications.info("rol-tenant-status", "⏳ Building template...");

    Promise.all([
      ApiTracker.fetch(ROL_DM() + "/organization-masters/position/roles", { headers: rolH() }, "Roles & Positions").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
      ApiTracker.fetch(ROL_DM() + "/organization-masters/position", { headers: rolH() }, "Roles & Positions").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
    ]).then(function (results) {
      var rolesRaw = results[0];
      var posList = results[1];
      var roles = Array.isArray(rolesRaw) ? rolesRaw : (rolesRaw && rolesRaw.data) || [];
      var rolesRows = roles.map(function (r) { return [r.id || "", r.roleName || r.name || "", r.description || "", r.onboarding ? "TRUE" : "FALSE", r.attendance ? "TRUE" : "FALSE", r.compliance ? "TRUE" : "FALSE", r.core ? "TRUE" : "FALSE"]; });

      var posSummary = Array.isArray(posList) ? posList : (posList && posList.data) || [];
      var posIds = posSummary.map(function (p) { return p.id; }).filter(Boolean);

      return rolFetchPositions(posIds).then(function (posDetails) {
        var posRows = [];
        posDetails.forEach(function (pos) { rolFlatPos(pos).forEach(function (r) { posRows.push(r); }); });

        downloadExcel("roles_positions_template.xlsx", [
          { name: "Positions_Upload", tabColor: "1D4ED8", headers: ROL_POS_HEADERS, rows: [], highlightCols: ROL_POS_INPUT },
          { name: "Roles_Master", tabColor: "059669", headers: ["id", "roleName", "description", "onboarding", "attendance", "compliance", "core"], rows: rolesRows },
          { name: "Existing_Positions", tabColor: "7C3AED", headers: ROL_VIEW_HEADERS, rows: posRows }
        ]);
        Notifications.success("rol-tenant-status", "✅ Template downloaded");
      });
    }).catch(function (e) {
      Notifications.error("rol-tenant-status", "❌ " + e.message);
    }).then(function () { btn.style.opacity = "1"; });
  }

  wireFileInput("rol-file", "rol-file-name", "rol-submit", "rol");

  document.getElementById("rol-dl-success").onclick = function () {
    downloadExcel("rol_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["id", "positionName", "action"], rows: (AppState.cache.rolSuccess || []).map(function (r) { return [r.id || "", r.name, r.action]; }) }]);
  };
  document.getElementById("rol-dl-failed").onclick = function () {
    downloadExcel("rol_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["positionName", "status", "error"], rows: (AppState.cache.rolFailed || []).map(function (r) { return [r.name, r.status || "", r.error || ""]; }) }]);
  };

  document.getElementById("rol-submit").onclick = function () {
    var btn = document.getElementById("rol-submit");
    var rows = AppState.cache.rol || [];
    Notifications.clearLog("rol-upload-log");
    document.getElementById("rol-dl-success").style.display = "none";
    document.getElementById("rol-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("rol-upload-status", "❌ No data"); return; }

    function col(row, name) {
      var norm = function (s) { return String(s).toLowerCase().replace(/[^a-z0-9]/g, ""); };
      var target = norm(name);
      var k = Object.keys(row).filter(function (k) { return norm(k) === target; })[0];
      return k ? String(row[k] || "").trim() : "";
    }
    var toBool = function (v) { return ["true", "1", "yes"].indexOf(String(v || "").toLowerCase().trim()) !== -1; };

    var updateGroups = {}, createGroups = {};
    rows.forEach(function (row) {
      var rawId = col(row, "id") || col(row, "id blankcreate");
      var pid = parseIntSafe(rawId);
      var name = col(row, "positionName");
      if (!name) return;
      if (pid !== null) { if (!updateGroups[pid]) updateGroups[pid] = []; updateGroups[pid].push(row); }
      else { if (!createGroups[name]) createGroups[name] = []; createGroups[name].push(row); }
    });

    var allGroups = Object.keys(updateGroups).map(function (id) { return { id: parseInt(id), grp: updateGroups[id], isUpdate: true }; })
      .concat(Object.keys(createGroups).map(function (name) { return { id: null, grp: createGroups[name], isUpdate: false }; }));
    if (!allGroups.length) { Notifications.error("rol-upload-status", "❌ No valid rows"); return; }

    Notifications.loading(btn, "Processing 0/" + allGroups.length + "...");
    Notifications.progress.show("rol-c-prog");
    AppState.cache.rolSuccess = []; AppState.cache.rolFailed = [];
    var s = 0, f = 0;

    function next(i) {
      if (i >= allGroups.length) return finish();
      var g = allGroups[i], grp = g.grp, first = grp[0], name = col(first, "positionName");
      Notifications.loading(btn, (i + 1) + "/" + allGroups.length + ": " + name + "...");

      var rolesSet = {};
      grp.forEach(function (row) {
        var raw = col(row, "roles") || col(row, "rolescommaseparated");
        raw.split(",").map(function (r) { return r.trim(); }).filter(Boolean).forEach(function (r) { rolesSet[r] = true; });
      });

      var payload = {
        positionName: name,
        activeStatus: toBool(col(first, "activeStatus") || "true"),
        deleted: false,
        personType: rolPersonType(col(first, "personType_id") || col(first, "persontypeid") || "1", col(first, "personType_description") || col(first, "persontypedescription")),
        roles: Object.keys(rolesSet),
        locationAccess: col(first, "locationAccess") || "",
        positionAccessIds: [],
        positionAccessRequired: toBool(col(first, "positionAccessRequired")),
        positionRequiredForDelegation: toBool(col(first, "positionRequiredForDelegation")),
        mandatoryLevels: []
      };
      // SAME URL for create and update — "id" in the body is what
      // distinguishes an update, confirmed against real API examples.
      if (g.isUpdate) payload.id = g.id;

      ApiTracker.fetch(ROL_DM() + "/organization-masters/position", { method: "POST", headers: rolH(), body: JSON.stringify(payload) }, "Roles & Positions").then(function (r) {
        return r.text().then(function (body) {
          if (r.ok) {
            var createdId = g.id || "";
            try { var parsed = JSON.parse(body); createdId = (parsed.data && parsed.data.id) || parsed.id || createdId; } catch (e) {}
            Notifications.log("rol-upload-log", "✅ " + (g.isUpdate ? "Updated" : "Created") + ": " + name + " (id:" + createdId + ", " + Object.keys(rolesSet).length + " role(s))", "ok");
            AppState.cache.rolSuccess.push({ id: createdId, name: name, action: g.isUpdate ? "Updated" : "Created" });
            Audit.onDbOp(g.isUpdate ? "updated" : "created", 1); s++;
          } else {
            var err = parseApiError(body);
            Notifications.log("rol-upload-log", "❌ Failed: " + name + " — " + err, "fail");
            AppState.cache.rolFailed.push({ name: name, status: r.status, error: err }); f++;
          }
        });
      }).catch(function (e) {
        Notifications.log("rol-upload-log", "❌ Error: " + name + " — " + e.message, "fail");
        AppState.cache.rolFailed.push({ name: name, status: "NET", error: e.message }); f++;
      }).then(function () {
        Notifications.progress.set("rol-c-bar", ((i + 1) / allGroups.length) * 100);
        next(i + 1);
      });
    }

    function finish() {
      Notifications.log("rol-upload-log", "━━━━━━━━━━━━━━━━━━", "info");
      Notifications.log("rol-upload-log", "✅ Success: " + s + "  ❌ Failed: " + f, f === 0 ? "ok" : "info");
      Notifications.status("rol-upload-status", "Done — " + s + " processed, " + f + " failed", f === 0 ? "success" : "info");
      Notifications.doneLoading(btn, "🚀 Create / Update Positions");
      Notifications.progress.hide("rol-c-prog");
      if (AppState.cache.rolSuccess.length) document.getElementById("rol-dl-success").style.display = "block";
      if (AppState.cache.rolFailed.length) document.getElementById("rol-dl-failed").style.display = "block";
    }

    next(0);
  };

  document.getElementById("rol-fetch").onclick = function () {
    var btn = document.getElementById("rol-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("rol-v-prog");
    Notifications.info("rol-view-status", "⏳ Fetching position list..."); Notifications.progress.set("rol-v-bar", 10);

    ApiTracker.fetch(ROL_DM() + "/organization-masters/position", { headers: rolH() }, "Roles & Positions").then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + parseApiError(t)); });
      return r.json();
    }).then(function (listRaw) {
      var posSummary = Array.isArray(listRaw) ? listRaw : (listRaw.data || []);
      var posIds = posSummary.map(function (p) { return p.id; }).filter(Boolean);
      if (!posIds.length) { Notifications.info("rol-view-status", "ℹ️ No positions found."); return; }

      Notifications.info("rol-view-status", "⏳ Fetching " + posIds.length + " positions individually..."); Notifications.progress.set("rol-v-bar", 25);
      return rolFetchPositions(posIds).then(function (details) {
        Notifications.info("rol-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("rol-v-bar", 80);

        var rows = [];
        details.forEach(function (pos) { rolFlatPos(pos).forEach(function (r) { rows.push(r); }); });

        return ApiTracker.fetch(ROL_DM() + "/organization-masters/position/roles", { headers: rolH() }, "Roles & Positions")
          .then(function (rr) { return rr.ok ? rr.json() : null; }).catch(function () { return null; })
          .then(function (rolesRaw) {
            var rList = Array.isArray(rolesRaw) ? rolesRaw : (rolesRaw && rolesRaw.data) || [];
            var rolesRows = rList.map(function (r) { return [r.id || "", r.roleName || r.name || "", r.description || "", r.onboarding ? "TRUE" : "FALSE", r.attendance ? "TRUE" : "FALSE", r.compliance ? "TRUE" : "FALSE", r.core ? "TRUE" : "FALSE"]; });

            downloadExcel("positions_" + new Date().toISOString().slice(0, 10) + ".xlsx", [
              { name: "Positions", tabColor: "1D4ED8", headers: ROL_VIEW_HEADERS, rows: rows },
              { name: "Roles_Master", tabColor: "059669", headers: ["id", "roleName", "description", "onboarding", "attendance", "compliance", "core"], rows: rolesRows }
            ]);
            Notifications.progress.set("rol-v-bar", 100);
            Notifications.success("rol-view-status", "✅ Download complete — " + details.length + " position(s), " + rows.length + " row(s)");
          });
      });
    }).catch(function (e) {
      Notifications.error("rol-view-status", "❌ " + e.message); Notifications.progress.set("rol-v-bar", 0);
    }).then(function () {
      Notifications.doneLoading(btn, "⬇️ Download All Positions");
      Notifications.progress.hide("rol-v-prog", 2500);
    });
  };

  console.log("✅ Roles & Positions module loaded — SUPERADMIN · x-organization-id tenant switching · single-URL create/update");
}