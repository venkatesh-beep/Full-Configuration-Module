/* =========================================================
 * tasks.js — BeeForce Configuration Portal
 * Plain script body. Executed as:
 *   new Function('AppCtx', <this file> + '\nreturn (typeof init==="function")?init(AppCtx):undefined;')
 * Defines a top-level `function init(ctx)` — nothing else is required.
 * No import/export syntax. ctx === AppCtx.
 * ========================================================= */
// =========================================================
// modules/tasks.js — BeeForce Configuration Portal
// Owns: screen-tasks, screen-tasks-view, screen-tasks-approve
// Endpoints:
//   GET  /api/attendance/workflow/tasks/mine?active.equals=true&onlyList=true
//   POST /api/attendance/workflow/tasks/mine/{id}   { action:"complete", taskFormData:{approved:true} }
// Exports: init(context)
// =========================================================

const TASK_TAB_COLORS = { "Task_IDs": "1D4ED8", "Timeoff": "059669", "Regularization": "D97706", "default": "7C3AED" };
const TASK_DESC_HEADERS = {
  "timeoff":        ["Name", "Employee Number", "Start Date", "End Date", "Paycode", "Paycode Description", "Leave Days"],
  "regularization": ["Name", "Employee Number", "Start Date", "End Date", "Reason", "In Time", "Out Time", "Day Type", "Field 9", "Field 10"],
  "default":        ["Name", "Employee Number", "Field 3", "Field 4", "Field 5", "Field 6", "Field 7", "Field 8", "Field 9", "Field 10"]
};

function taskTypeKey(processDefinitionId) {
  if (!processDefinitionId) return "unknown";
  return String(processDefinitionId).split(":")[0].toLowerCase().replace(/_/g, " ");
}
function taskTypeName(processDefinitionId) {
  const k = taskTypeKey(processDefinitionId);
  return k.charAt(0).toUpperCase() + k.slice(1);
}
function safeSheetName(name) { return name.replace(/[:\\/?*[\]]/g, "").substring(0, 31); }
function parseDesc(description) {
  if (!description) return [];
  return String(description).split("|").map(s => s.trim());
}
function buildTaskRow(task) {
  const typeKey = taskTypeKey(task.processDefinitionId || "");
  const descHeaders = TASK_DESC_HEADERS[typeKey] || TASK_DESC_HEADERS["default"];
  const descValues = parseDesc(task.description);
  while (descValues.length < descHeaders.length) descValues.push("");
  const row = [task.id || "", task.name || "", task.priority || "", task.processDefinitionId || "",
    task.processInstanceId || "", task.createTime || "", task.formKey || ""];
  descHeaders.forEach((_, i) => row.push(descValues[i] || ""));
  return row;
}
function buildTypeHeaders(typeKey) {
  const descHeaders = TASK_DESC_HEADERS[typeKey] || TASK_DESC_HEADERS["default"];
  return ["id", "name", "priority", "processDefinitionId", "processInstanceId", "createTime", "formKey", ...descHeaders];
}

function init(ctx) {
  const { AppState, apiH, downloadExcel, wireFileInput, parseApiError, cleanTaskId, Notifications, Router, Audit, ApiTracker, modal } = ctx;

  if (!document.getElementById("screen-tasks")) {
    const main = document.createElement("div");
    main.id = "screen-tasks"; main.style.display = "none";
    main.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-cur">✅ Tasks</span></div>
      <div class="bf-module-header"><div class="mh-icon">✅</div><div><div class="mh-title">Pending Tasks</div><div class="mh-sub">Fetch · Download by type · Bulk Approve</div></div></div>
      <div class="bf-action-grid">
        <div class="bf-action-card" id="tasks-action-fetch">
          <div class="ac-icon">⬇️</div><div class="ac-name">Download Tasks</div>
          <div class="ac-desc">Fetches all pending tasks and downloads Excel automatically</div>
        </div>
        <div class="bf-action-card" id="tasks-action-approve">
          <div class="ac-icon">✅</div><div class="ac-name">Upload & Approve Tasks</div>
          <div class="ac-desc">Upload task IDs from Task_IDs sheet to bulk approve</div>
        </div>
      </div>`;
    modal.appendChild(main);

    const view = document.createElement("div");
    view.id = "screen-tasks-view"; view.style.display = "none";
    view.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-tasks">✅ Tasks</span><span class="bc-sep">›</span><span class="bc-cur">Download Tasks</span></div>
      <div id="tasks-view-status" class="bf-status"></div>
      <div class="bf-progress" id="tasks-v-prog" style="display:none"><div class="bf-pb" id="tasks-v-bar" style="width:0%"></div></div>
      <button class="bf-btn bf-primary" id="tasks-dl-main">⬇️ Download Pending Tasks</button>`;
    modal.appendChild(view);

    const approve = document.createElement("div");
    approve.id = "screen-tasks-approve"; approve.style.display = "none";
    approve.innerHTML = `
      <div class="bf-breadcrumb"><span class="bc-link" data-go="screen-hub">🏠 Home</span><span class="bc-sep">›</span><span class="bc-link" data-go="screen-tasks">✅ Tasks</span><span class="bc-sep">›</span><span class="bc-cur">Upload & Approve</span></div>
      <div class="bf-info-box">
        Upload a file with an <b>id</b> column (use the Task_IDs sheet from the downloaded Excel).<br>
        Only the task <b>id</b> is needed — name/description/type columns are ignored.
      </div>
      <div id="tasks-approve-status" class="bf-status"></div>
      <label class="bf-file-label" for="tasks-file"><span id="tasks-file-name">📂 Click to select Task_IDs file (.xlsx)</span></label>
      <input type="file" id="tasks-file" class="bf-file-input" accept=".xlsx,.xls,.csv" />
      <div class="bf-progress" id="tasks-prog"><div class="bf-pb" id="tasks-bar" style="width:0%"></div></div>
      <div class="bf-log" id="tasks-approve-log"></div>
      <button class="bf-btn bf-success" id="tasks-approve-btn" disabled>✅ Approve Tasks</button>`;
    modal.appendChild(approve);

    Router.register("screen-tasks", "screen-tasks-view", "screen-tasks-approve");
    [main, view, approve].forEach(el => {
      Router.wireDataGoLinks(el);
      el.querySelectorAll("input,textarea").forEach(inp =>
        ["keydown", "keyup", "keypress", "input"].forEach(evt => inp.addEventListener(evt, e => e.stopPropagation(), true))
      );
    });
  }

  document.getElementById("tasks-action-fetch").onclick = () => Router.go("screen-tasks-view");
  document.getElementById("tasks-action-approve").onclick = () => {
    Notifications.clearLog("tasks-approve-log");
    AppState.cache.tasks = null;
    document.getElementById("tasks-approve-btn").disabled = true;
    document.getElementById("tasks-file-name").textContent = "📂 Click to select Task_IDs file (.xlsx)";
    Router.go("screen-tasks-approve");
  };

  async function tasksDownloadNow() {
    const prog = document.getElementById("tasks-v-prog");
    const bar = document.getElementById("tasks-v-bar");
    const dlBtn = document.getElementById("tasks-dl-main");
    if (dlBtn) dlBtn.disabled = true;
    Notifications.progress.show("tasks-v-prog");
    Notifications.progress.set("tasks-v-bar", 0);

    try {
      Notifications.info("tasks-view-status", "⏳ Connecting to server..."); Notifications.progress.set("tasks-v-bar", 15);
      const r = await ApiTracker.fetch(`${AppState.BASE_URL}/api/attendance/workflow/tasks/mine?active.equals=true&onlyList=true`, { headers: apiH() }, "Tasks");
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${parseApiError(await r.text())}`);

      Notifications.info("tasks-view-status", "⏳ Fetching pending tasks..."); Notifications.progress.set("tasks-v-bar", 35);
      const tasks = await r.json();

      if (!tasks || !tasks.length) { Notifications.info("tasks-view-status", "ℹ️ No pending tasks found."); return; }

      Notifications.info("tasks-view-status", `⏳ Processing ${tasks.length} task(s)...`); Notifications.progress.set("tasks-v-bar", 60);

      const grouped = {};
      tasks.forEach(t => {
        const typeName = taskTypeName(t.processDefinitionId || "unknown");
        if (!grouped[typeName]) grouped[typeName] = [];
        grouped[typeName].push(t);
      });
      AppState.cache.tasksData = { tasks, grouped };

      Notifications.info("tasks-view-status", "⏳ Preparing Excel file..."); Notifications.progress.set("tasks-v-bar", 80);

      const sheets = [];
      sheets.push({
        name: "Task_IDs", tabColor: TASK_TAB_COLORS["Task_IDs"],
        headers: ["id", "task_name", "type"],
        rows: tasks.map(t => [t.id, t.name || "", taskTypeName(t.processDefinitionId || "")])
      });
      Object.entries(grouped).forEach(([typeName, list]) => {
        const typeKey = taskTypeKey(list[0].processDefinitionId || "");
        sheets.push({
          name: safeSheetName(typeName),
          tabColor: TASK_TAB_COLORS[typeName] || TASK_TAB_COLORS["default"],
          headers: buildTypeHeaders(typeKey),
          rows: list.map(t => buildTaskRow(t))
        });
      });

      Notifications.info("tasks-view-status", "⏳ Downloading..."); Notifications.progress.set("tasks-v-bar", 95);
      downloadExcel(`pending_tasks_${new Date().toISOString().slice(0, 10)}.xlsx`, sheets);

      Notifications.progress.set("tasks-v-bar", 100);
      const typeCount = Object.keys(grouped).length;
      Notifications.success("tasks-view-status", `✅ Download complete — ${tasks.length} task(s) across ${typeCount} type(s)`);
      Notifications.progress.hide("tasks-v-prog", 2000);
    } catch (e) {
      Notifications.error("tasks-view-status", `❌ ${e.message}`); Notifications.progress.set("tasks-v-bar", 0);
      Notifications.progress.hide("tasks-v-prog", 3000);
    } finally {
      if (dlBtn) { dlBtn.disabled = false; dlBtn.innerHTML = "⬇️ Download Pending Tasks"; }
    }
  }
  document.getElementById("tasks-dl-main").onclick = () => tasksDownloadNow();

  wireFileInput("tasks-file", "tasks-file-name", "tasks-approve-btn", "tasks");

  document.getElementById("tasks-approve-btn").onclick = async () => {
    const btn = document.getElementById("tasks-approve-btn");
    const rows = AppState.cache.tasks || [];
    Notifications.clearLog("tasks-approve-log");

    if (!rows.length) { Notifications.error("tasks-approve-status", "❌ No data found in file"); return; }

    const idCol = Object.keys(rows[0]).find(k => k.trim().toLowerCase() === "id");
    if (!idCol) { Notifications.error("tasks-approve-status", "❌ No 'id' column found in uploaded file"); return; }

    const ids = rows.map(r => cleanTaskId(r[idCol])).filter(id => id !== "");
    if (!ids.length) { Notifications.error("tasks-approve-status", "❌ No task IDs found in file"); return; }

    Notifications.loading(btn, `Approving 0/${ids.length}...`);
    Notifications.progress.show("tasks-prog");

    let s = 0, f = 0;
    for (let i = 0; i < ids.length; i++) {
      const taskId = ids[i];
      try {
        const payload = { id: taskId, action: "complete", taskFormData: { approved: true } };
        const r = await ApiTracker.fetch(`${AppState.BASE_URL}/api/attendance/workflow/tasks/mine/${taskId}`, {
          method: "POST", headers: apiH(), body: JSON.stringify(payload)
        }, "Tasks");

        if (r.status === 200 || r.status === 201 || r.status === 204) {
          Notifications.log("tasks-approve-log", `✅ Approved: ${taskId}`, "ok"); s++;
        } else {
          const errText = parseApiError(await r.text());
          Notifications.log("tasks-approve-log", `❌ Failed: ${taskId} — HTTP ${r.status}: ${errText}`, "fail"); f++;
        }
      } catch (e) {
        Notifications.log("tasks-approve-log", `❌ Error: ${taskId} — ${e.message}`, "fail"); f++;
      }

      Notifications.progress.set("tasks-bar", ((i + 1) / ids.length) * 100);
      Notifications.loading(btn, `Approving ${i + 1}/${ids.length}...`);
    }

    Audit.onDbOp("updated", s);
    Notifications.log("tasks-approve-log", "━━━━━━━━━━━━━━━━━━", "info");
    Notifications.log("tasks-approve-log", `✅ Approved: ${s}  ❌ Failed: ${f}`, f === 0 ? "ok" : "info");
    Notifications.status("tasks-approve-status", `Done — ${s} approved, ${f} failed`, f === 0 ? "success" : "info");
    Notifications.doneLoading(btn, "✅ Approve Tasks");
    Notifications.progress.hide("tasks-prog");
  };
}
