import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { stringify } from 'csv-stringify/sync';

dotenv.config({ path: new URL('../.env', import.meta.url).pathname });

const app = express();
app.use(cors());
app.use(express.json());

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'Logs@BT';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '8684##';
const PORT = process.env.PORT || 4000;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment.');
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

const applyFilters = (query, filters = {}) => {
  const { username, module, action, search, startDate, endDate } = filters;

  if (username) query = query.eq('username', username);
  if (module) query = query.eq('module', module);
  if (action) query = query.eq('action', action);

  if (startDate) query = query.gte('created_at', `${startDate}T00:00:00.000Z`);
  if (endDate) query = query.lte('created_at', `${endDate}T23:59:59.999Z`);

  if (search) {
    const escaped = search.replace(/,/g, '');
    query = query.or(`username.ilike.%${escaped}%,module.ilike.%${escaped}%,action.ilike.%${escaped}%`);
  }

  return query;
};

const normalizePagination = (page, pageSize) => {
  const safePage = Math.max(1, Number.parseInt(page, 10) || 1);
  const safePageSize = [10, 20].includes(Number.parseInt(pageSize, 10))
    ? Number.parseInt(pageSize, 10)
    : 10;
  const from = (safePage - 1) * safePageSize;
  const to = from + safePageSize - 1;
  return { safePage, safePageSize, from, to };
};

app.post('/api/admin/login', (req, res) => {
  const { username, password } = req.body;

  if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
    return res.json({ success: true, token: 'admin-logs-session' });
  }

  return res.status(401).json({ success: false, message: 'Unauthorized' });
});

app.use('/api/admin', (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (token !== 'admin-logs-session') {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  return next();
});

app.get('/api/admin/logs', async (req, res) => {
  const { page = 1, pageSize = 10, username, module, action, search, startDate, endDate } = req.query;

  const { safePage, safePageSize, from, to } = normalizePagination(page, pageSize);

  let query = supabase
    .from('logs')
    .select('id, username, module, action, file_name, file_url, ip_address, created_at', { count: 'exact' })
    .order('created_at', { ascending: false })
    .range(from, to);

  query = applyFilters(query, { username, module, action, search, startDate, endDate });

  const { data, error, count } = await query;

  if (error) {
    return res.status(500).json({ message: error.message });
  }

  return res.json({
    rows: data || [],
    totalCount: count || 0,
    page: safePage,
    pageSize: safePageSize,
    totalPages: Math.max(1, Math.ceil((count || 0) / safePageSize))
  });
});

app.get('/api/admin/logs/options', async (_req, res) => {
  const [uRes, mRes] = await Promise.all([
    supabase.from('logs').select('username').not('username', 'is', null),
    supabase.from('logs').select('module').not('module', 'is', null)
  ]);

  if (uRes.error || mRes.error) {
    return res.status(500).json({
      message: uRes.error?.message || mRes.error?.message || 'Failed loading filter options.'
    });
  }

  const usernames = [...new Set((uRes.data || []).map((r) => r.username).filter(Boolean))].sort();
  const modules = [...new Set((mRes.data || []).map((r) => r.module).filter(Boolean))].sort();

  return res.json({ usernames, modules });
});

app.get('/api/admin/logs/download-all', async (req, res) => {
  const { username, module, action, search, startDate, endDate } = req.query;

  let query = supabase
    .from('logs')
    .select('username, module, action, created_at, file_name')
    .order('created_at', { ascending: false });

  query = applyFilters(query, { username, module, action, search, startDate, endDate });

  const { data, error } = await query;

  if (error) return res.status(500).json({ message: error.message });

  const csv = stringify(data || [], {
    header: true,
    columns: ['username', 'module', 'action', 'created_at', 'file_name']
  });

  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename="logs-export-all.csv"');
  return res.status(200).send(csv);
});

app.listen(PORT, () => {
  console.log(`Admin Logs backend running at http://localhost:${PORT}`);
});
