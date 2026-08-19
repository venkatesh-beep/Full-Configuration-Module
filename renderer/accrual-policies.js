/* =========================================================
 * accrual-policies.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 *
 * Owns: screen-accrpol, screen-accrpol-create, screen-accrpol-view, screen-accrpol-delete
 * GET    /api/attendance/accrual_policies/{id}?attributes=paycodes,grantPaycodes,cascades
 * POST   /api/attendance/accrual_policies/
 * PUT    /api/attendance/accrual_policies/{id}?attributes=paycodes,grantPaycodes,cascades
 * DELETE /api/attendance/accrual_policies/{id}
 *
 * RELATIONAL 8-SHEET STRUCTURE (replaces the old single-sheet cartesian
 * product, which produced hundreds of duplicate rows per policy):
 *   1. Accrual_Policy        — one row per policy, no Policy Key
 *   2. Grant_Amounts         — Policy Key + Grant Amounts - *
 *   3. Grant_Amount_Rules    — Policy Key + Grant Amount Rules - *
 *   4. Grant_Prorations      — Policy Key + Grant Prorations - *
 *   5. Termination_Prorations— Policy Key + Termination Prorations - *
 *   6. Grant_Roundings       — Policy Key + Grant Roundings - *
 *   7. Paycodes              — Policy Key + Type (GRANT/TAKING) +
 *                              Grant Paycodes - * + Taking Paycodes - *
 *                              (only the relevant pair is populated per row)
 *   8. Accrual_Cascades      — Policy Key + Accrual Cascades - *
 *
 * Policy Key = the policy's Name (Sheet 1). Every child sheet links
 * back to its policy purely by matching Name — this applies for BOTH
 * create and update; only Sheet 1's own ID decides create vs update.
 *
 * ALL header text below is copied verbatim from the original
 * ACCRPOL_HEADERS — nothing renamed, abbreviated, or simplified.
 *
 * NOT covered by any column (always forced false in the payload):
 * carryoverAmountMax, prioritizeCarryoverBalance, carryoverEncashmentAmountMax,
 * terminationEncashmentAmountMax, manualEncashmentAmountMax.
 * ========================================================= */

// Master list of every original header, in original order — used only
// as the single source of truth for exact header text (sliced below
// into each sheet). Never modify these strings.
const ACCRPOL_HEADERS = [
  "ID", "Name", "Accrual ID", "Description",
  "Grant Information - Type", "Grant Information - Frequency", "Grant Information - Start Date(YYYY-MM-DD)", "Grant Information - Force Avail",
  "Grant Expiration - Expiration", "Grant Expiration - Expired After",
  "Grant Amounts - Start", "Grant Amounts - End", "Grant Amounts - Amount", "Grant Amounts - Max",
  "Grant Amount Rules - Condition", "Grant Amount Rules - Value",
  "Grant Prorations - Start Date(MM/DD)", "Grant Prorations - End Date(MM/DD)", "Grant Prorations - Amount",
  "Termination Prorations - Start Date(MM/DD)", "Termination Prorations - End Date(MM/DD)", "Termination Prorations - Amount",
  "Grant Roundings - Start", "Grant Roundings - End", "Grant Roundings - Value",
  "Grant Paycodes - Paycode ID", "Grant Paycodes - Amount",
  "Taking Paycodes - Paycode ID", "Taking Paycodes - Amount",
  "Accrual Cascades - Accrual ID", "Accrual Cascades - Priority"
];

// Original per-group colors — preserved exactly, applied per-column
// within Sheet 1 (which merges 3 original groups) and as a uniform
// header color for each single-purpose child sheet.
const COLOR = {
  basic: { bg: "E5E7EB", font: "111827" },
  grantInfo: { bg: "2563EB", font: "FFFFFF" },
  grantExpiration: { bg: "16A34A", font: "FFFFFF" },
  grantAmounts: { bg: "7C3AED", font: "FFFFFF" },
  grantProrations: { bg: "D97706", font: "FFFFFF" },
  termProrations: { bg: "DB2777", font: "FFFFFF" },
  roundings: { bg: "0D9488", font: "FFFFFF" },
  grantPaycodes: { bg: "4F46E5", font: "FFFFFF" },
  takingPaycodes: { bg: "EA580C", font: "FFFFFF" },
  cascades: { bg: "DC2626", font: "FFFFFF" },
  key: { bg: "E5E7EB", font: "111827" } // Policy Key / Type columns
};

// SHEET 1 — Accrual_Policy (indices 0-9 of ACCRPOL_HEADERS, no Policy Key)
const SHEET1_HEADERS = ACCRPOL_HEADERS.slice(0, 10);
const SHEET1_COLORS = [COLOR.basic, COLOR.basic, COLOR.basic, COLOR.basic, COLOR.grantInfo, COLOR.grantInfo, COLOR.grantInfo, COLOR.grantInfo, COLOR.grantExpiration, COLOR.grantExpiration];
const SHEET1_INPUT_COLS = [1, 2, 3, 4, 5, 6];

// SHEET 2 — Grant_Amounts
const SHEET2_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(10, 14)];
const SHEET2_COLORS = [COLOR.key, COLOR.grantAmounts, COLOR.grantAmounts, COLOR.grantAmounts, COLOR.grantAmounts];

// SHEET 3 — Grant_Amount_Rules
const SHEET3_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(14, 16)];
const SHEET3_COLORS = [COLOR.key, COLOR.grantAmounts, COLOR.grantAmounts];

// SHEET 4 — Grant_Prorations
const SHEET4_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(16, 19)];
const SHEET4_COLORS = [COLOR.key, COLOR.grantProrations, COLOR.grantProrations, COLOR.grantProrations];

// SHEET 5 — Termination_Prorations
const SHEET5_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(19, 22)];
const SHEET5_COLORS = [COLOR.key, COLOR.termProrations, COLOR.termProrations, COLOR.termProrations];

// SHEET 6 — Grant_Roundings
const SHEET6_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(22, 25)];
const SHEET6_COLORS = [COLOR.key, COLOR.roundings, COLOR.roundings, COLOR.roundings];

// SHEET 7 — Paycodes (combined Grant + Taking, distinguished by Type)
const SHEET7_HEADERS = ["Policy Key", "Type", ...ACCRPOL_HEADERS.slice(25, 29)];
const SHEET7_COLORS = [COLOR.key, COLOR.key, COLOR.grantPaycodes, COLOR.grantPaycodes, COLOR.takingPaycodes, COLOR.takingPaycodes];

// SHEET 8 — Accrual_Cascades
const SHEET8_HEADERS = ["Policy Key", ...ACCRPOL_HEADERS.slice(29, 31)];
const SHEET8_COLORS = [COLOR.key, COLOR.cascades, COLOR.cascades];

function toHeaderColors(colorArr) { return colorArr; }

function init(ctx) {
  const { AppState, apiH, downloadExcel, parseApiError, parseIntSafe, Notifications, Router, Audit, ApiTracker, fetchPaycodesRef, modal } = ctx;
  const ACCRPOL_BASE = () => `${AppState.BASE_URL}/api/attendance/accrual_policies`;
  const ACCR_MASTER_URL = () => `${AppState.BASE_URL}/api/attendance/accruals`;
  const ATTR_QS = "attributes=paycodes,grantPaycodes,cascades";

  const col = (row, name) => {
    const n = name.toLowerCase().replace(/[^a-z0-9]/g, "");
    const k = Object.keys(row).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, "") === n);
    return k ? String(row[k] || "").trim() : "";
  };
  const toBool = v => ["true", "1", "yes"].includes(String(v || "").toLowerCase().trim());
  const toNum = v => { const n = parseFloat(v); return isNaN(n) ? null : n; };
  const ts = v => (v === null || v === undefined) ? "" : typeof v === "boolean" ? (v ? "TRUE" : "FALSE") : String(v);

  // -------------------------------------------------------
  // FLATTEN: one policy -> rows for each of the 8 sheets
  // -------------------------------------------------------
  function flattenPolicy(p) {
    const accrual = p.accrual || {};
    const key = p.name || "";
    const sheet1 = [ts(p.id), ts(p.name), ts(accrual.id), ts(p.description), ts(p.grantType), ts(p.grantFrequency), p.grantStartDate || "", ts(p.forceAvail), ts(p.grantExpiration), ts(p.grantExpiredAfter)];

    const sheet2 = (p.grantAmounts || []).map(a => [key, ts(a.start), ts(a.end), ts(a.amount), ts(a.max)]);
    const sheet3 = (p.grantAmountRules || []).map(r => [key, ts(r.condition), ts(r.value)]);
    const sheet4 = (p.grantProrations || []).map(pr => [key, pr.startDate || "", pr.endDate || "", ts(pr.amount)]);
    const sheet5 = (p.grantTerminationProrations || []).map(tp => [key, tp.startDate || "", tp.endDate || "", ts(tp.amount)]);
    const sheet6 = (p.grantRoundings || []).map(rd => [key, ts(rd.start), ts(rd.end), ts(rd.value)]);
    const sheet7 = [
      ...(p.grantPaycodes || []).map(gp => [key, "GRANT", ts(gp.paycode && gp.paycode.id), ts(gp.amount), "", ""]),
      ...(p.paycodes || []).map(tk => [key, "TAKING", "", "", ts(tk.paycode && tk.paycode.id), ts(tk.amount)])
    ];
    const sheet8 = (p.cascades || []).map(cs => [key, ts(cs.accrual && cs.accrual.id), ts(cs.priority)]);

    return { sheet1, sheet2, sheet3, sheet4, sheet5, sheet6, sheet7, sheet8 };
  }

  async function accrPolFetchAll() {
    let r = await ApiTracker.fetch(`${ACCRPOL_BASE()}?projection=FULL`, { headers: apiH() }, "Accrual Policies");
    if (!r.ok) r = await ApiTracker.fetch(`${ACCRPOL_BASE()}/`, { headers: apiH() }, "Accrual Policies");
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);
    const raw = await r.json();
    const summary = Array.isArray(raw) ? raw : (raw.content || raw.data || []);
    const CONCURRENCY = 8;
    const full = [];
    for (let i = 0; i < summary.length; i += CONCURRENCY) {
      const batch = summary.slice(i, i + CONCURRENCY);
      const settled = await Promise.allSettled(batch.map(p =>
        ApiTracker.fetch(`${ACCRPOL_BASE()}/${p.id}?${ATTR_QS}`, { headers: apiH() }, "Accrual Policies").then(rr => rr.ok ? rr.json() : p)
      ));
      settled.forEach(s => full.push(s.status === "fulfilled" ? s.value : null));
    }
    return full.filter(Boolean);
  }

  async function accrFetchMaster() {
    const r = await ApiTracker.fetch(ACCR_MASTER_URL(), { headers: apiH() }, "Accrual Policies");
    if (!r.ok) return [];
    const raw = await r.json();
    return Array.isArray(raw) ? raw : (raw.content || raw.data || []);
  }

  // -------------------------------------------------------
  // UI shell
  // -------------------------------------------------------
  if (!document.getElementById("screen-accrpol")) {
    const main = document.createElement("div");
    main.id = "screen-accrpol"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">📜 Accrual Policies</span></div>
      <div class="bf-module-header"><div class="mh-icon">📜</div><div><div class="mh-title">Accrual Policies</div><div class="mh-sub">Create · Update · View · Delete — relational 8-sheet format</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="accrpol-action-tpl"><div class="ac-icon">⬇️</div><div class="ac-name">Download Template</div><div class="ac-desc">8 upload sheets · 8 existing-data ref sheets · paycodes/accruals master</div></div>
        <div class="bf-action-card" id="accrpol-action-create"><div class="ac-icon">📤</div><div class="ac-name">Upload & Create/Update</div><div class="ac-desc">Sheet 1 ID blank = create; child sheets link by Policy Key = Name</div></div>
        <div class="bf-action-card" id="accrpol-action-view"><div class="ac-icon">📋</div><div class="ac-name">View Existing</div><div class="ac-desc">Same 8-sheet structure, populated</div></div>
        <div class="bf-action-card" id="accrpol-action-delete"><div class="ac-icon">🗑️</div><div class="ac-name">Delete</div><div class="ac-desc">Delete policies by comma-separated IDs</div></div>
      </div>
      <div id="accrpol-tpl-status" class="bf-status" style="margin-top:14px;"></div>`;
    modal.appendChild(main);

    const create = document.createElement("div");
    create.id = "screen-accrpol-create"; create.style.display = "none";
    create.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrpol">📜 Accrual Policies</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Create/Update</span></div>
      <div class="bf-info-box">
        Upload the file with all 8 sheets present (<code>Accrual_Policy</code>, <code>Grant_Amounts</code>, <code>Grant_Amount_Rules</code>, <code>Grant_Prorations</code>, <code>Termination_Prorations</code>, <code>Grant_Roundings</code>, <code>Paycodes</code>, <code>Accrual_Cascades</code>).<br>
        Sheet 1's <b>ID</b> blank = create; filled = update. Every child sheet's <b>Policy Key</b> must exactly match the policy's <b>Name</b> in Sheet 1.<br>
        In <b>Paycodes</b>, set <b>Type</b> to <code>GRANT</code> or <code>TAKING</code> and fill only the matching pair of columns.
      </div>
      <div id="accrpol-create-status" class="bf-status"></div>
      <label class="bf-file-label" for="accrpol-file"><span id="accrpol-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="accrpol-file" class="bf-file-input" accept=".xlsx,.xls" />
      <div class="bf-progress" id="accrpol-c-prog"><div class="bf-pb" id="accrpol-c-bar" style="width:0%"></div></div>
      <div class="bf-log" id="accrpol-create-log"></div>
      <button class="bf-btn bf-success" id="accrpol-submit" disabled>🚀 Create / Update Policies</button>
      <button class="bf-btn bf-outline" id="accrpol-cancel">✕ Cancel Upload</button>
      <button class="bf-btn bf-outline" id="accrpol-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="accrpol-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(create);

    const view = document.createElement("div");
    view.id = "screen-accrpol-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrpol">📜 Accrual Policies</span><span class="bc-sep">›</span><span class="bc-cur">View Existing</span></div>
      <div id="accrpol-view-status" class="bf-status"></div>
      <div class="bf-progress" id="accrpol-v-prog" style="display:none"><div class="bf-pb" id="accrpol-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="accrpol-fetch">⬇️ Download Accrual Policies</button>`;
    modal.appendChild(view);

    const del = document.createElement("div");
    del.id = "screen-accrpol-delete"; del.style.display = "none";
    del.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-accrpol">📜 Accrual Policies</span><span class="bc-sep">›</span><span class="bc-cur">Delete</span></div>
      <div class="bf-warn-box">⚠️ Deletion is permanent and cannot be undone.</div>
      <div id="accrpol-delete-status" class="bf-status"></div>
      <label class="bf-label">Policy IDs to delete (comma-separated)</label>
      <input type="text" id="accrpol-del-ids" placeholder="259, 260, 261" />
      <label class="bf-label" style="display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:400;"><input type="checkbox" id="accrpol-confirm" style="width:auto;margin:0;" />I understand this is permanent</label>
      <div class="bf-log" id="accrpol-delete-log"></div>
      <button class="bf-btn bf-danger" id="accrpol-do-delete" style="margin-top:10px;">🗑️ Delete</button>`;
    modal.appendChild(del);

    Router.register("screen-accrpol", "screen-accrpol-create", "screen-accrpol-view", "screen-accrpol-delete");
    [main, create, view, del].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  // -------------------------------------------------------
  // Download Template — 8 blank upload sheets + 8 populated "_Existing"
  // reference sheets + Paycodes_Master + Accruals_Master
  // -------------------------------------------------------
  document.getElementById("accrpol-action-tpl").onclick = async () => {
    const btn = document.getElementById("accrpol-action-tpl"); btn.style.opacity = "0.6";
    Notifications.status("accrpol-tpl-status", "⏳ Building template...", "info");
    const [polRes, pcRes, accRes] = await Promise.allSettled([accrPolFetchAll().catch(() => []), fetchPaycodesRef(), accrFetchMaster()]);
    const policies = polRes.status === "fulfilled" ? polRes.value : [];
    const paycodes = pcRes.status === "fulfilled" ? pcRes.value : [];
    const accruals = accRes.status === "fulfilled" ? accRes.value : [];

    const existing = { s1: [], s2: [], s3: [], s4: [], s5: [], s6: [], s7: [], s8: [] };
    policies.forEach(p => {
      const f = flattenPolicy(p);
      existing.s1.push(f.sheet1); existing.s2.push(...f.sheet2); existing.s3.push(...f.sheet3);
      existing.s4.push(...f.sheet4); existing.s5.push(...f.sheet5); existing.s6.push(...f.sheet6);
      existing.s7.push(...f.sheet7); existing.s8.push(...f.sheet8);
    });

    downloadExcel("accrual_policies_template.xlsx", [
      { name: "Accrual_Policy", tabColor: "0369A1", headers: SHEET1_HEADERS, rows: [], highlightCols: SHEET1_INPUT_COLS, headerColors: SHEET1_COLORS },
      { name: "Grant_Amounts", tabColor: "7C3AED", headers: SHEET2_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET2_COLORS },
      { name: "Grant_Amount_Rules", tabColor: "7C3AED", headers: SHEET3_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET3_COLORS },
      { name: "Grant_Prorations", tabColor: "D97706", headers: SHEET4_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET4_COLORS },
      { name: "Termination_Prorations", tabColor: "DB2777", headers: SHEET5_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET5_COLORS },
      { name: "Grant_Roundings", tabColor: "0D9488", headers: SHEET6_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET6_COLORS },
      { name: "Paycodes", tabColor: "4F46E5", headers: SHEET7_HEADERS, rows: [], highlightCols: [0, 1], headerColors: SHEET7_COLORS },
      { name: "Accrual_Cascades", tabColor: "DC2626", headers: SHEET8_HEADERS, rows: [], highlightCols: [0], headerColors: SHEET8_COLORS },
      { name: "Accrual_Policy_Existing", tabColor: "94A3B8", headers: SHEET1_HEADERS, rows: existing.s1, headerColors: SHEET1_COLORS },
      { name: "Grant_Amounts_Existing", tabColor: "94A3B8", headers: SHEET2_HEADERS, rows: existing.s2, headerColors: SHEET2_COLORS },
      { name: "Grant_Amount_Rules_Existing", tabColor: "94A3B8", headers: SHEET3_HEADERS, rows: existing.s3, headerColors: SHEET3_COLORS },
      { name: "Grant_Prorations_Existing", tabColor: "94A3B8", headers: SHEET4_HEADERS, rows: existing.s4, headerColors: SHEET4_COLORS },
      { name: "Termination_Prorations_Existing", tabColor: "94A3B8", headers: SHEET5_HEADERS, rows: existing.s5, headerColors: SHEET5_COLORS },
      { name: "Grant_Roundings_Existing", tabColor: "94A3B8", headers: SHEET6_HEADERS, rows: existing.s6, headerColors: SHEET6_COLORS },
      { name: "Paycodes_Existing", tabColor: "94A3B8", headers: SHEET7_HEADERS, rows: existing.s7, headerColors: SHEET7_COLORS },
      { name: "Accrual_Cascades_Existing", tabColor: "94A3B8", headers: SHEET8_HEADERS, rows: existing.s8, headerColors: SHEET8_COLORS },
      { name: "Paycodes_Master", tabColor: "059669", headers: ["id", "code", "description"], rows: paycodes.map(p => [p.id, p.code || "", p.description || ""]) },
      { name: "Accruals_Master", tabColor: "1D4ED8", headers: ["id", "name", "description"], rows: accruals.map(a => [a.id, a.name || "", a.description || ""]) }
    ]);
    Notifications.success("accrpol-tpl-status", `✅ Template downloaded — ${policies.length} existing polic${policies.length === 1 ? "y" : "ies"}, ${paycodes.length} paycode(s), ${accruals.length} accrual(s)`);
    btn.style.opacity = "1";
  };

  document.getElementById("accrpol-action-create").onclick = () => {
    Notifications.clearLog("accrpol-create-log"); AppState.cache.accrpolSheets = null; AppState.cache.accrpolSuccess = []; AppState.cache.accrpolFailed = [];
    document.getElementById("accrpol-submit").disabled = true;
    document.getElementById("accrpol-dl-success").style.display = "none";
    document.getElementById("accrpol-dl-failed").style.display = "none";
    document.getElementById("accrpol-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    document.getElementById("accrpol-file").value = "";
    Router.go("screen-accrpol-create");
  };
  document.getElementById("accrpol-action-view").onclick = () => Router.go("screen-accrpol-view");
  document.getElementById("accrpol-action-delete").onclick = () => { Notifications.clearLog("accrpol-delete-log"); Router.go("screen-accrpol-delete"); };

  document.getElementById("accrpol-cancel").onclick = () => {
    AppState.cache.accrpolSheets = null;
    document.getElementById("accrpol-file").value = "";
    document.getElementById("accrpol-file-name").textContent = "📂 Click to select filled template (.xlsx)";
    document.getElementById("accrpol-submit").disabled = true;
    Notifications.clearLog("accrpol-create-log");
    document.getElementById("accrpol-create-status").className = "bf-status";
    document.getElementById("accrpol-create-status").textContent = "";
    Router.go("screen-accrpol");
  };

  // -------------------------------------------------------
  // Custom multi-sheet file reader — reads all 8 named sheets, not
  // just the first one (unlike the shared wireFileInput helper).
  // -------------------------------------------------------
  document.getElementById("accrpol-file").addEventListener("change", (e) => {
    const file = e.target.files[0];
    const submitBtn = document.getElementById("accrpol-submit");
    if (!file) { AppState.cache.accrpolSheets = null; submitBtn.disabled = true; return; }
    document.getElementById("accrpol-file-name").textContent = "📄 " + file.name;

    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const wb = XLSX.read(new Uint8Array(ev.target.result), { type: "array" });
        const readSheet = (name) => {
          const ws = wb.Sheets[name];
          return ws ? XLSX.utils.sheet_to_json(ws, { defval: "", raw: false }) : [];
        };
        const sheets = {
          policy: readSheet("Accrual_Policy"),
          grantAmounts: readSheet("Grant_Amounts"),
          grantAmountRules: readSheet("Grant_Amount_Rules"),
          grantProrations: readSheet("Grant_Prorations"),
          terminationProrations: readSheet("Termination_Prorations"),
          grantRoundings: readSheet("Grant_Roundings"),
          paycodes: readSheet("Paycodes"),
          cascades: readSheet("Accrual_Cascades")
        };
        if (!sheets.policy.length) {
          Notifications.alert("❌ 'Accrual_Policy' sheet is empty or missing — nothing to submit.");
          AppState.cache.accrpolSheets = null; submitBtn.disabled = true; return;
        }
        AppState.cache.accrpolSheets = sheets;
        submitBtn.disabled = false;
        if (Audit) Audit.onFileSelected(file.name);
      } catch (err) {
        Notifications.alert("❌ Failed to read file: " + err.message);
        AppState.cache.accrpolSheets = null; submitBtn.disabled = true;
      }
    };
    reader.onerror = () => { Notifications.alert("❌ Failed to read file"); submitBtn.disabled = true; };
    reader.readAsArrayBuffer(file);
  });

  document.getElementById("accrpol-dl-success").onclick = () => {
    downloadExcel("accrpol_success.xlsx", [{ name: "Success", tabColor: "059669", headers: ["policy_id", "name", "action"], rows: (AppState.cache.accrpolSuccess || []).map(r => [r.id || "", r.name, r.action]) }]);
  };
  document.getElementById("accrpol-dl-failed").onclick = () => {
    downloadExcel("accrpol_failed.xlsx", [{ name: "Failed", tabColor: "DC2626", headers: ["name", "http_status", "error"], rows: (AppState.cache.accrpolFailed || []).map(r => [r.name, r.status || "", r.error || ""]) }]);
  };

  function buildPayloadForPolicy(polRow, sheets) {
    const key = col(polRow, "Name");
    const matches = (rows) => rows.filter(r => col(r, "Policy Key") === key);

    const grantAmounts = matches(sheets.grantAmounts).map(r => {
      const s = col(r, "Grant Amounts - Start"), e = col(r, "Grant Amounts - End"), amt = col(r, "Grant Amounts - Amount"), mx = col(r, "Grant Amounts - Max");
      const o = { start: s, end: e }; if (amt) o.amount = amt; o.max = toBool(mx); return o;
    });
    const grantAmountRules = matches(sheets.grantAmountRules).map(r => ({ condition: col(r, "Grant Amount Rules - Condition"), value: col(r, "Grant Amount Rules - Value") })).filter(r => r.condition);
    const grantProrations = matches(sheets.grantProrations).map(r => ({ startDate: col(r, "Grant Prorations - Start Date(MM/DD)"), endDate: col(r, "Grant Prorations - End Date(MM/DD)"), amount: toNum(col(r, "Grant Prorations - Amount")) || 0 }));
    const grantTerminationProrations = matches(sheets.terminationProrations).map(r => ({ startDate: col(r, "Termination Prorations - Start Date(MM/DD)"), endDate: col(r, "Termination Prorations - End Date(MM/DD)"), amount: toNum(col(r, "Termination Prorations - Amount")) || 0 }));
    const grantRoundings = matches(sheets.grantRoundings).map(r => ({ start: col(r, "Grant Roundings - Start"), end: col(r, "Grant Roundings - End"), value: col(r, "Grant Roundings - Value") }));
    const paycodeRows = matches(sheets.paycodes);
    const grantPaycodes = paycodeRows.filter(r => col(r, "Type").toUpperCase() === "GRANT").map(r => ({ paycode: { id: parseIntSafe(col(r, "Grant Paycodes - Paycode ID")) }, amount: toNum(col(r, "Grant Paycodes - Amount")) || 0 })).filter(x => x.paycode.id !== null);
    const takingPaycodes = paycodeRows.filter(r => col(r, "Type").toUpperCase() === "TAKING").map(r => ({ paycode: { id: parseIntSafe(col(r, "Taking Paycodes - Paycode ID")) }, amount: toNum(col(r, "Taking Paycodes - Amount")) || 0 })).filter(x => x.paycode.id !== null);
    const cascades = matches(sheets.cascades).map(r => ({ accrual: { id: parseIntSafe(col(r, "Accrual Cascades - Accrual ID")) }, priority: parseIntSafe(col(r, "Accrual Cascades - Priority")) || 1 })).filter(x => x.accrual.id !== null);

    const payload = {
      name: key,
      description: col(polRow, "Description") || key,
      accrual: { id: parseIntSafe(col(polRow, "Accrual ID")) },
      grantType: col(polRow, "Grant Information - Type") || "FIXED_EARNED",
      grantFrequency: col(polRow, "Grant Information - Frequency") || "MONTHLY",
      grantStartDate: col(polRow, "Grant Information - Start Date(YYYY-MM-DD)"),
      forceAvail: toBool(col(polRow, "Grant Information - Force Avail")),
      grantExpiration: col(polRow, "Grant Expiration - Expiration"),
      carryoverAmountMax: false,
      prioritizeCarryoverBalance: false,
      carryoverEncashmentAmountMax: false,
      terminationEncashmentAmountMax: false,
      manualEncashmentAmountMax: false
    };
    const expiredAfter = col(polRow, "Grant Expiration - Expired After");
    if (expiredAfter) payload.grantExpiredAfter = parseIntSafe(expiredAfter);

    if (grantAmounts.length) payload.grantAmounts = grantAmounts;
    if (grantAmountRules.length) payload.grantAmountRules = grantAmountRules;
    if (grantProrations.length) payload.grantProrations = grantProrations;
    if (grantTerminationProrations.length) payload.grantTerminationProrations = grantTerminationProrations;
    if (grantRoundings.length) payload.grantRoundings = grantRoundings;
    if (grantPaycodes.length) payload.grantPaycodes = grantPaycodes;
    if (takingPaycodes.length) payload.paycodes = takingPaycodes;
    if (cascades.length) payload.cascades = cascades;

    const polId = parseIntSafe(col(polRow, "ID"));
    return { key, polId, payload };
  }

  document.getElementById("accrpol-submit").onclick = async () => {
    const btn = document.getElementById("accrpol-submit");
    const sheets = AppState.cache.accrpolSheets;
    Notifications.clearLog("accrpol-create-log");
    document.getElementById("accrpol-dl-success").style.display = "none";
    document.getElementById("accrpol-dl-failed").style.display = "none";
    if (!sheets || !sheets.policy.length) { Notifications.error("accrpol-create-status", "❌ No data found"); return; }

    const entries = sheets.policy.map(row => buildPayloadForPolicy(row, sheets)).filter(e => e.key);
    const total = entries.length;
    if (!total) { Notifications.error("accrpol-create-status", "❌ No valid policy rows found in Accrual_Policy sheet"); return; }

    Notifications.loading(btn, `Processing 0/${total} polic${total === 1 ? "y" : "ies"}...`);
    Notifications.progress.show("accrpol-c-prog");
    AppState.cache.accrpolSuccess = []; AppState.cache.accrpolFailed = [];
    let s = 0, f = 0, done = 0;

    for (const entry of entries) {
      const { key, polId, payload } = entry;
      const isUpdate = polId !== null;
      if (isUpdate) payload.id = polId;
      try {
        const url = isUpdate ? `${ACCRPOL_BASE()}/${polId}?${ATTR_QS}` : `${ACCRPOL_BASE()}/`;
        const r = await ApiTracker.fetch(url, { method: isUpdate ? "PUT" : "POST", headers: apiH(), body: JSON.stringify(payload) }, "Accrual Policies");
        const body = await r.text();
        if (r.ok) {
          let rid = polId || "";
          if (!isUpdate) { try { rid = JSON.parse(body).id || ""; } catch (e) {} }
          Notifications.log("accrpol-create-log", `✅ ${isUpdate ? "Updated" : "Created"}: "${key}"`, "ok");
          AppState.cache.accrpolSuccess.push({ id: rid, name: key, action: isUpdate ? "Updated" : "Created" });
          Audit.onDbOp(isUpdate ? "updated" : "created", 1); s++;
        } else {
          const err = parseApiError(body);
          Notifications.log("accrpol-create-log", `❌ ${isUpdate ? "Update" : "Create"} failed: "${key}" — ${err}`, "fail");
          AppState.cache.accrpolFailed.push({ name: key, status: r.status, error: err }); f++;
        }
      } catch (e) {
        Notifications.log("accrpol-create-log", `❌ Error: "${key}" — ${e.message}`, "fail");
        AppState.cache.accrpolFailed.push({ name: key, status: "NET", error: e.message }); f++;
      }
      done++; Notifications.progress.set("accrpol-c-bar", (done / total) * 100);
      Notifications.loading(btn, `Processing ${done}/${total}...`);
    }

    Notifications.log("accrpol-create-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("accrpol-create-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("accrpol-create-status", `Done — ${s} processed, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🚀 Create / Update Policies");
    Notifications.progress.hide("accrpol-c-prog");
    if (AppState.cache.accrpolSuccess.length) document.getElementById("accrpol-dl-success").style.display = "block";
    if (AppState.cache.accrpolFailed.length) document.getElementById("accrpol-dl-failed").style.display = "block";
  };

  document.getElementById("accrpol-fetch").onclick = async () => {
    const btn = document.getElementById("accrpol-fetch");
    Notifications.loading(btn, "Connecting...");
    Notifications.progress.show("accrpol-v-prog");
    try {
      Notifications.info("accrpol-view-status", "⏳ Fetching accrual policies..."); Notifications.progress.set("accrpol-v-bar", 20);
      const list = await accrPolFetchAll();
      if (!list.length) { Notifications.info("accrpol-view-status", "ℹ️ No accrual policies found."); return; }
      Notifications.info("accrpol-view-status", `⏳ Flattening ${list.length} polic${list.length === 1 ? "y" : "ies"}...`); Notifications.progress.set("accrpol-v-bar", 55);

      const out = { s1: [], s2: [], s3: [], s4: [], s5: [], s6: [], s7: [], s8: [] };
      list.forEach(p => {
        const f = flattenPolicy(p);
        out.s1.push(f.sheet1); out.s2.push(...f.sheet2); out.s3.push(...f.sheet3);
        out.s4.push(...f.sheet4); out.s5.push(...f.sheet5); out.s6.push(...f.sheet6);
        out.s7.push(...f.sheet7); out.s8.push(...f.sheet8);
      });

      Notifications.info("accrpol-view-status", "⏳ Preparing Excel..."); Notifications.progress.set("accrpol-v-bar", 85);
      downloadExcel(`accrual_policies_${new Date().toISOString().slice(0, 10)}.xlsx`, [
        { name: "Accrual_Policy", tabColor: "0369A1", headers: SHEET1_HEADERS, rows: out.s1, headerColors: SHEET1_COLORS },
        { name: "Grant_Amounts", tabColor: "7C3AED", headers: SHEET2_HEADERS, rows: out.s2, headerColors: SHEET2_COLORS },
        { name: "Grant_Amount_Rules", tabColor: "7C3AED", headers: SHEET3_HEADERS, rows: out.s3, headerColors: SHEET3_COLORS },
        { name: "Grant_Prorations", tabColor: "D97706", headers: SHEET4_HEADERS, rows: out.s4, headerColors: SHEET4_COLORS },
        { name: "Termination_Prorations", tabColor: "DB2777", headers: SHEET5_HEADERS, rows: out.s5, headerColors: SHEET5_COLORS },
        { name: "Grant_Roundings", tabColor: "0D9488", headers: SHEET6_HEADERS, rows: out.s6, headerColors: SHEET6_COLORS },
        { name: "Paycodes", tabColor: "4F46E5", headers: SHEET7_HEADERS, rows: out.s7, headerColors: SHEET7_COLORS },
        { name: "Accrual_Cascades", tabColor: "DC2626", headers: SHEET8_HEADERS, rows: out.s8, headerColors: SHEET8_COLORS }
      ]);
      Notifications.progress.set("accrpol-v-bar", 100);
      Notifications.success("accrpol-view-status", `✅ Download complete — ${list.length} polic${list.length === 1 ? "y" : "ies"}`);
    } catch (e) {
      Notifications.error("accrpol-view-status", `❌ ${e.message}`); Notifications.progress.set("accrpol-v-bar", 0);
    } finally {
      Notifications.doneLoading(btn, "⬇️ Download Accrual Policies");
      Notifications.progress.hide("accrpol-v-prog", 2500);
    }
  };

  document.getElementById("accrpol-do-delete").onclick = async () => {
    if (!document.getElementById("accrpol-confirm").checked) { Notifications.error("accrpol-delete-status", "⚠️ Check confirmation box"); return; }
    const ids = document.getElementById("accrpol-del-ids").value.split(",").map(s => s.trim()).filter(s => s !== "");
    if (!ids.length) { Notifications.error("accrpol-delete-status", "❌ No IDs entered"); return; }
    const btn = document.getElementById("accrpol-do-delete");
    Notifications.loading(btn, "Deleting..."); Notifications.clearLog("accrpol-delete-log");
    let s = 0, f = 0;
    for (const id of ids) {
      try {
        const r = await ApiTracker.fetch(`${ACCRPOL_BASE()}/${id}`, { method: "DELETE", headers: apiH() }, "Accrual Policies");
        if (r.status === 200 || r.status === 204 || r.status === 201) { Notifications.log("accrpol-delete-log", `✅ Deleted: ${id}`, "ok"); s++; }
        else { Notifications.log("accrpol-delete-log", `❌ Failed: ${id} — ${parseApiError(await r.text())}`, "fail"); f++; }
      } catch (e) { Notifications.log("accrpol-delete-log", `❌ Error: ${id} — ${e.message}`, "fail"); f++; }
    }
    Audit.onDbOp("deleted", s);
    Notifications.status("accrpol-delete-status", `Done — ${s} deleted, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "🗑️ Delete");
  };

  console.log("✅ Accrual Policies loaded — relational 8-sheet structure, exact header names preserved");
}