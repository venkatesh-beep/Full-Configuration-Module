import { supabase } from './supabaseClient';

const ADMIN_USER = 'Logs@BT';
const ADMIN_PASS = '8684##';

export function handleAdminShortcutLogin(usernameInput, passwordInput) {
  const username = usernameInput.trim();
  const password = passwordInput.trim();

  console.debug('[Login] Trimmed username:', username);
  console.debug('[Login] Checking admin shortcut condition...');

  if (username === ADMIN_USER && password === ADMIN_PASS) {
    console.debug('[Login] Admin shortcut condition matched. Redirecting to /admin-logs');
    localStorage.setItem('isAdmin', 'true');
    localStorage.setItem('authUser', ADMIN_USER);
    return { isAdmin: true, username };
  }

  console.debug('[Login] Admin shortcut condition not matched. Continue with normal login flow.');
  return { isAdmin: false, username, password };
}

export async function normalLogin(username, password) {
  console.debug('[Login] Calling normal login API flow...');
  // Integrate your existing API here.
  if (!username || !password) {
    throw new Error('Username and password are required.');
  }
  return { success: true };
}

function applyFilters(query, filters = {}) {
  const { username, module, action, startDate, endDate, search } = filters;

  if (username) query = query.eq('username', username);
  if (module) query = query.eq('module', module);
  if (action) query = query.ilike('action', `%${action}%`);
  if (startDate) query = query.gte('created_at', `${startDate}T00:00:00.000Z`);
  if (endDate) query = query.lte('created_at', `${endDate}T23:59:59.999Z`);

  if (search?.trim()) {
    const term = search.trim().replace(/,/g, '');
    query = query.or(`username.ilike.%${term}%,module.ilike.%${term}%,action.ilike.%${term}%`);
  }

  return query;
}

export async function fetchLogs({ page = 1, pageSize = 10, ...filters }) {
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  let query = supabase
    .from('logs')
    .select('id, username, module, action, file_name, file_url, created_at', { count: 'exact' })
    .order('created_at', { ascending: false })
    .range(from, to);

  query = applyFilters(query, filters);

  const { data, error, count } = await query;
  if (error) throw error;

  return {
    rows: data || [],
    totalCount: count || 0,
    totalPages: Math.max(1, Math.ceil((count || 0) / pageSize))
  };
}

export async function fetchFilterOptions() {
  const { data, error } = await supabase.from('logs').select('username,module').limit(5000);
  if (error) throw error;

  const usernames = [...new Set((data || []).map((i) => i.username).filter(Boolean))].sort();
  const modules = [...new Set((data || []).map((i) => i.module).filter(Boolean))].sort();
  return { usernames, modules };
}

export function exportCsv(rows) {
  const header = ['username', 'module', 'action', 'created_at', 'file_name'];
  const csv = [header, ...rows.map((r) => [r.username, r.module, r.action, r.created_at, r.file_name])]
    .map((line) => line.map((v) => `"${String(v || '').replaceAll('"', '""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'logs-filtered.csv';
  link.click();
  URL.revokeObjectURL(url);
}
