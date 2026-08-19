/* =========================================================
 * punch.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/punch.js — BeeForce Configuration Portal
// Owns: screen-pun, screen-pun-single, screen-pun-bulk
// Endpoint: POST /api/attendance/punches/action/
//   Without Direction → action:"ADD_NO_TYPE"
//   With Direction    → action:"ADD" + punchType:"IN"|"OUT"
//
// FIX: bulk uploads normalize the punchTime column through
// punNormalizeDateTime() before sending — Excel silently reformats
// typed datetimes (different separators/order/AM-PM) depending on
// regional settings, so what you typed and what SheetJS reads back
// can differ from the exact "YYYY-MM-DD HH:MM:SS" the API needs. This
// is why Single Entry (a plain text box Excel can't touch) worked
// while Bulk Upload 400'd.
//
// Also adds a Cancel button that stops the bulk loop between rows.
// ========================================================= */
function init(ctx) {
  const { AppState, downloadExcel, wireFileInput, parseApiError, Notifications, Router, Audit, ApiTracker, modal } = ctx;
  const PUN_URL = () => `${AppState.BASE_URL}/api/attendance/punches/action/`;

  // ── Inject screens (only once) ──────────────────────────
  if (!document.getElementById("screen-pun")) {
    const main = document.createElement("div");
    main.id = "screen-pun"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">👊 Punch</span></div>
      <div class="bf-module-header"><div class="mh-icon">👊</div><div><div class="mh-title">Punch</div><div class="mh-sub">Single Entry · Bulk Upload · With or Without Direction</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="pun-action-single"><div class="ac-icon">📝</div><div class="ac-name">Single Entry</div><div class="ac-desc">Enter one punch manually (with or without direction)</div></div>
        <div class="bf-action-card" id="pun-action-bulk"><div class="ac-icon">📤</div><div class="ac-name">Bulk Upload</div><div class="ac-desc">Download template, fill and upload (with or without direction)</div></div>
      </div>`;
    modal.appendChild(main);

    const single = document.createElement("div");
    single.id = "screen-pun-single"; single.style.display = "none";
    single.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pun">👊 Punch</span><span class="bc-sep">›</span><span class="bc-cur">Single Entry</span></div>
      <div id="pun-s-status" class="bf-status"></div>
      <label class="bf-label">Punch Direction</label>
      <div class="pun-dir-toggle" id="pun-s-dir-toggle">
        <button class="pun-dir-btn active" data-dir="no-dir">Without Direction (ADD_NO_TYPE)</button>
        <button class="pun-dir-btn" data-dir="with-dir">With Direction (ADD)</button>
      </div>
      <div class="bf-grid3" style="margin-bottom:0">
        <div style="grid-column:1/3"><label class="bf-label">External Number</label><input type="text" id="pun-s-ext" placeholder="K1004062" /></div>
        <div id="pun-s-type-wrap" style="display:none">
          <label class="bf-label">Punch Type</label>
          <select id="pun-s-type"><option value="IN">IN</option><option value="OUT">OUT</option></select>
        </div>
      </div>
      <label class="bf-label">Punch Time (YYYY-MM-DD HH:MM:SS)</label>
      <input type="text" id="pun-s-time" placeholder="2026-07-14 06:50:00" />
      <button class="bf-btn bf-success" id="pun-s-submit">👊 Submit Punch</button>`;
    modal.appendChild(single);

    const bulk = document.createElement("div");
    bulk.id = "screen-pun-bulk"; bulk.style.display = "none";
    bulk.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-pun">👊 Punch</span><span class="bc-sep">›</span><span class="bc-cur">Bulk Upload</span></div>
      <div class="bf-info-box">
        <b>Without Direction:</b> columns = externalNumber, punchTime<br>
        <b>With Direction:</b> columns = externalNumber, punchTime, punchType (IN/OUT)<br>
        Dates/times are auto-normalized regardless of how Excel reformats them, so any common format works.
      </div>
      <label class="bf-label">Template Type</label>
      <div class="pun-dir-toggle" id="pun-b-dir-toggle">
        <button class="pun-dir-btn active" data-dir="no-dir">Without Direction</button>
        <button class="pun-dir-btn" data-dir="with-dir">With Direction</button>
      </div>
      <button class="bf-btn bf-outline" id="pun-b-tpl">⬇️ Download Template</button>
      <div id="pun-b-status" class="bf-status"></div>
      <label class="bf-file-label" for="pun-b-file"><span id="pun-b-file-name">📂 Click to select filled template (.xlsx)</span></label>
      <input type="file" id="pun-b-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="pun-b-prog"><div class="bf-pb" id="pun-b-bar" style="width:0%"></div></div>
      <div id="pun-b-counter" style="font-size:12px;color:#6B7280;text-align:center;margin-bottom:6px;"></div>
      <div class="bf-log" id="pun-b-log"></div>
      <div style="display:flex;gap:8px;">
        <button class="bf-btn bf-success" id="pun-b-submit" disabled style="flex:1;">🚀 Submit Punches</button>
        <button class="bf-btn bf-danger" id="pun-b-cancel" style="display:none;flex:1;">⛔ Cancel Upload</button>
      </div>
      <button class="bf-btn bf-outline" id="pun-b-dl-success" style="display:none">⬇️ Download Success Report</button>
      <button class="bf-btn bf-outline" id="pun-b-dl-failed"  style="display:none">⬇️ Download Failed Report</button>`;
    modal.appendChild(bulk);

    Router.register("screen-pun", "screen-pun-single", "screen-pun-bulk");
    [main, single, bulk].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea,select").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  // ── Action cards ─────────────────────────────────────────
  document.getElementById("pun-action-single").onclick = () => Router.go("screen-pun-single");
  document.getElementById("pun-action-bulk").onclick = () => {
    Notifications.clearLog("pun-b-log");
    AppState.cache.punBulk = null; AppState.cache.punSuccess = []; AppState.cache.punFailed = [];
    document.getElementById("pun-b-submit").disabled = true;
    document.getElementById("pun-b-cancel").style.display = "none";
    document.getElementById("pun-b-dl-success").style.display = "none";
    document.getElementById("pun-b-dl-failed").style.display = "none";
    document.getElementById("pun-b-counter").textContent = "";
    Router.go("screen-pun-bulk");
  };

  // ── Direction toggles ────────────────────────────────────
  function wireDirToggle(toggleId, onChange) {
    const toggle = document.getElementById(toggleId);
    if (!toggle) return;
    toggle.querySelectorAll(".pun-dir-btn").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        toggle.querySelectorAll(".pun-dir-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        onChange(btn.dataset.dir === "with-dir");
      });
    });
  }
  wireDirToggle("pun-s-dir-toggle", withDir => {
    document.getElementById("pun-s-type-wrap").style.display = withDir ? "block" : "none";
  });
  wireDirToggle("pun-b-dir-toggle", () => {});

  function punBuildBody(externalNumber, punchTime, withDir, punchType) {
    const body = { action: withDir ? "ADD" : "ADD_NO_TYPE", punch: { employee: { externalNumber }, punchTime } };
    if (withDir && punchType) body.punch.punchType = punchType;
    return body;
  }

  var PUN_MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

  /**
   * Normalizes whatever Excel handed back for a punch datetime into the
   * exact "YYYY-MM-DD HH:MM:SS" the API requires. Handles the formats
   * Excel commonly reformats a typed datetime into depending on locale.
   */
  function punNormalizeDateTime(val) {
    if (!val) return "";
    var s = String(val).trim();

    // Already exact target format
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(s)) return s;

    // ISO with 'T' separator: 2026-07-14T06:50:00
    var isoT = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})[T ](\d{1,2}):(\d{2})(?::(\d{2}))?/);
    if (isoT) {
      return isoT[1] + "-" + z(isoT[2]) + "-" + z(isoT[3]) + " " + z(isoT[4]) + ":" + isoT[5] + ":" + (isoT[6] || "00");
    }

    // M/D/YYYY HH:MM[:SS] [AM/PM] (Excel US default)
    var us = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})[ ,]+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?/);
    if (us) {
      var hh = parseInt(us[4], 10);
      if (us[7]) {
        var pm = /pm/i.test(us[7]);
        if (pm && hh < 12) hh += 12;
        if (!pm && hh === 12) hh = 0;
      }
      return us[3] + "-" + z(us[1]) + "-" + z(us[2]) + " " + z(hh) + ":" + us[5] + ":" + (us[6] || "00");
    }

    // D-MMM-YY(YY) HH:MM[:SS] e.g. "14-Jul-26 06:50"
    var monMatch = s.match(/^(\d{1,2})-([A-Za-z]{3,})-(\d{2,4})[ ,]+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM|am|pm)?/);
    if (monMatch) {
      var mon = PUN_MONTHS[monMatch[2].slice(0, 3).toLowerCase()];
      if (mon) {
        var yr = monMatch[3].length === 2 ? ("20" + monMatch[3]) : monMatch[3];
        var h2 = parseInt(monMatch[4], 10);
        if (monMatch[7]) {
          var pm2 = /pm/i.test(monMatch[7]);
          if (pm2 && h2 < 12) h2 += 12;
          if (!pm2 && h2 === 12) h2 = 0;
        }
        return yr + "-" + z(mon) + "-" + z(monMatch[1]) + " " + z(h2) + ":" + monMatch[5] + ":" + (monMatch[6] || "00");
      }
    }

    // Last resort — let the browser's Date parser take a shot
    var d = new Date(s.replace(" ", "T"));
    if (!isNaN(d.getTime())) {
      return d.getFullYear() + "-" + z(d.getMonth() + 1) + "-" + z(d.getDate()) + " " + z(d.getHours()) + ":" + z(d.getMinutes()) + ":" + z(d.getSeconds());
    }
    return s; // give up — pass through unchanged so the failure log shows exactly what was sent

    function z(n) { return ("0" + n).slice(-2); }
  }

  // ── Single Entry submit ──────────────────────────────────
  document.getElementById("pun-s-submit").onclick = async () => {
    const btn = document.getElementById("pun-s-submit");
    const ext = document.getElementById("pun-s-ext").value.trim();
    const time = document.getElementById("pun-s-time").value.trim();
    const withDir = document.querySelector("#pun-s-dir-toggle .pun-dir-btn.active")?.dataset.dir === "with-dir";
    const punchType = withDir ? document.getElementById("pun-s-type").value : "";

    if (!ext || !time) { Notifications.error("pun-s-status", "❌ External Number and Punch Time are required"); return; }

    Notifications.loading(btn, "Submitting...");
    try {
      const body = punBuildBody(ext, time, withDir, punchType);
      const r = await ApiTracker.fetch(PUN_URL(), { method: "POST", headers: ctx.apiH(), body: JSON.stringify(body) }, "Punch");
      const respBody = await r.text();
      if (r.status === 200 || r.status === 201 || r.status === 202) {
        Audit.onDbOp("created", 1);
        Notifications.success("pun-s-status", `✅ Punch submitted — ext: ${ext} | time: ${time}${withDir ? " | " + punchType : ""}`);
      } else {
        Notifications.error("pun-s-status", `❌ Failed — ${parseApiError(respBody)}`);
      }
    } catch (e) {
      Notifications.error("pun-s-status", `❌ ${e.message}`);
    } finally {
      Notifications.doneLoading(btn, "👊 Submit Punch");
    }
  };

  // ── Bulk template download ───────────────────────────────
  document.getElementById("pun-b-tpl").onclick = () => {
    const withDir = document.querySelector("#pun-b-dir-toggle .pun-dir-btn.active")?.dataset.dir === "with-dir";
    if (withDir) {
      downloadExcel("punch_with_direction_template.xlsx", [{
        name: "Punch_With_Direction", tabColor: "1D4ED8",
        headers: ["externalNumber", "punchTime (YYYY-MM-DD HH:MM:SS)", "punchType (IN/OUT)"],
        rows: [], highlightCols: [0, 1, 2]
      }]);
    } else {
      downloadExcel("punch_no_direction_template.xlsx", [{
        name: "Punch_No_Direction", tabColor: "059669",
        headers: ["externalNumber", "punchTime (YYYY-MM-DD HH:MM:SS)"],
        rows: [], highlightCols: [0, 1]
      }]);
    }
  };

  wireFileInput("pun-b-file", "pun-b-file-name", "pun-b-submit", "punBulk");

  document.getElementById("pun-b-dl-success").onclick = () => {
    downloadExcel("punch_success.xlsx", [{
      name: "Success", tabColor: "059669",
      headers: ["externalNumber", "punchTime", "direction", "punchType"],
      rows: (AppState.cache.punSuccess || []).map(r => [r.ext, r.time, r.dir, r.type || ""])
    }]);
  };
  document.getElementById("pun-b-dl-failed").onclick = () => {
    downloadExcel("punch_failed.xlsx", [{
      name: "Failed", tabColor: "DC2626",
      headers: ["externalNumber", "punchTime", "direction", "punchType", "error"],
      rows: (AppState.cache.punFailed || []).map(r => [r.ext, r.time, r.dir, r.type || "", r.error || ""])
    }]);
  };

  // ── Cancel wiring ─────────────────────────────────────────
  let punCancelRequested = false;
  document.getElementById("pun-b-cancel").onclick = () => {
    punCancelRequested = true;
    Notifications.log("pun-b-log", "⛔ Cancel requested — stopping after the current row...", "info");
    document.getElementById("pun-b-cancel").disabled = true;
  };

  // ── Bulk submit ───────────────────────────────────────────
  document.getElementById("pun-b-submit").onclick = async () => {
    const btn = document.getElementById("pun-b-submit");
    const cancelBtn = document.getElementById("pun-b-cancel");
    const counterEl = document.getElementById("pun-b-counter");
    const rows = AppState.cache.punBulk || [];
    Notifications.clearLog("pun-b-log");
    document.getElementById("pun-b-dl-success").style.display = "none";
    document.getElementById("pun-b-dl-failed").style.display = "none";
    if (!rows.length) { Notifications.error("pun-b-status", "❌ No data"); return; }

    const col = (row, name) => {
      const n = name.toLowerCase().replace(/[^a-z0-9]/g, "");
      const k = Object.keys(row).find(k => k.toLowerCase().replace(/[^a-z0-9]/g, "") === n);
      return k ? String(row[k] || "").trim() : "";
    };

    const hasDir = Object.keys(rows[0]).some(k => k.toLowerCase().includes("punchtype") || k.toLowerCase().includes("direction"));

    punCancelRequested = false;
    cancelBtn.style.display = "block";
    cancelBtn.disabled = false;
    btn.style.display = "none";
    Notifications.loading(btn, `Processing 0/${rows.length}...`);
    Notifications.progress.show("pun-b-prog");
    Notifications.progress.set("pun-b-bar", 0);
    AppState.cache.punSuccess = []; AppState.cache.punFailed = [];
    let s = 0, f = 0, cancelledAt = -1;

    for (let i = 0; i < rows.length; i++) {
      if (punCancelRequested) { cancelledAt = i; break; }

      const row = rows[i];
      const ext = col(row, "externalNumber") || col(row, "externalnumber");
      const rawTime = col(row, "punchTime") || col(row, "punchtime") || col(row, "punchtimeyyyymmddhhmmss");
      const time = punNormalizeDateTime(rawTime);

      if (!ext || !time) {
        AppState.cache.punFailed.push({ ext, time, dir: "", type: "", error: "Missing externalNumber or punchTime" });
        Audit.onValidationError(`Punch bulk row ${i + 2}: missing externalNumber or punchTime`);
        f++;
      } else {
        const rawDir = (col(row, "direction") || "").toUpperCase();
        const rawType = (col(row, "punchType") || col(row, "punchtypeinout") || "").toUpperCase();
        const withDir = hasDir && (rawDir === "ADD" || rawType === "IN" || rawType === "OUT" || rawDir === "WITH");
        const punchType = withDir ? (rawType || "IN") : "";

        try {
          const body = punBuildBody(ext, time, withDir, punchType);
          const r = await ApiTracker.fetch(PUN_URL(), { method: "POST", headers: ctx.apiH(), body: JSON.stringify(body) }, "Punch");
          const respBody = await r.text();
          if (r.status === 200 || r.status === 201 || r.status === 202) {
            AppState.cache.punSuccess.push({ ext, time, dir: withDir ? "ADD" : "ADD_NO_TYPE", type: punchType });
            s++;
          } else {
            const err = parseApiError(respBody);
            Notifications.log("pun-b-log", `❌ ext: ${ext} | time: ${time} | ${err}`, "fail");
            AppState.cache.punFailed.push({ ext, time, dir: withDir ? "ADD" : "ADD_NO_TYPE", type: punchType, error: err });
            f++;
          }
        } catch (e) {
          Notifications.log("pun-b-log", `❌ ext: ${ext} | ${e.message}`, "fail");
          AppState.cache.punFailed.push({ ext, time, dir: "", type: "", error: e.message });
          f++;
        }
      }

      Notifications.progress.set("pun-b-bar", ((i + 1) / rows.length) * 100);
      Notifications.loading(btn, `Processing ${i + 1}/${rows.length}...`);
      counterEl.textContent = `${i + 1} / ${rows.length} processed — ✅ ${s}  ❌ ${f}`;
    }

    Audit.onDbOp("created", s);
    Notifications.progress.done("pun-b-bar");
    Notifications.log("pun-b-log", "━━━━━━━━━━━━━━━━━━", "info");
    if (cancelledAt >= 0) {
      Notifications.log("pun-b-log", `⛔ Cancelled at row ${cancelledAt + 2} — ${rows.length - cancelledAt} row(s) not attempted`, "info");
    }
    Notifications.log("pun-b-log", `✅ Success: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status(
      "pun-b-status",
      cancelledAt >= 0
        ? `Cancelled — ${s} submitted, ${f} failed, ${rows.length - cancelledAt} skipped`
        : `Done — ${s} submitted, ${f} failed`,
      f === 0 && cancelledAt < 0 ? "success" : "info"
    );
    Notifications.doneLoading(btn, "🚀 Submit Punches");
    btn.style.display = "block";
    cancelBtn.style.display = "none";
    Notifications.progress.hide("pun-b-prog", 2500);
    if (AppState.cache.punSuccess.length) document.getElementById("pun-b-dl-success").style.display = "block";
    if (AppState.cache.punFailed.length) document.getElementById("pun-b-dl-failed").style.display = "block";
  };
}