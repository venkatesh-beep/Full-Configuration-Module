const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000';

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('adminToken') || ''}`
});

export async function adminLogin(username, password) {
  const response = await fetch(`${API_BASE}/api/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) throw new Error('Invalid admin credentials');
  return response.json();
}

export async function fetchFilterOptions() {
  const response = await fetch(`${API_BASE}/api/admin/logs/options`, {
    headers: authHeaders()
  });
  if (!response.ok) throw new Error('Failed to fetch filter options');
  return response.json();
}

export async function fetchLogs(params) {
  const query = new URLSearchParams(params);
  const response = await fetch(`${API_BASE}/api/admin/logs?${query.toString()}`, {
    headers: authHeaders()
  });

  if (!response.ok) throw new Error('Failed to fetch logs');
  return response.json();
}

export function exportCsv(filteredRows) {
  const header = ['username', 'module', 'action', 'created_at', 'file_name'];
  const rows = filteredRows.map((row) => [
    row.username || '',
    row.module || '',
    row.action || '',
    row.created_at || '',
    row.file_name || ''
  ]);
  const csvBody = [header, ...rows]
    .map((line) => line.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csvBody], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'logs-filtered.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadAllLogs(params) {
  const query = new URLSearchParams(params);
  window.open(`${API_BASE}/api/admin/logs/download-all?${query.toString()}`, '_blank');
}
