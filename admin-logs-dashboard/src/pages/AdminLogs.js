import React, { useEffect, useMemo, useState } from 'react';
import LogsTable from '../components/LogsTable';
import { adminLogin, downloadAllLogs, exportCsv, fetchFilterOptions, fetchLogs } from '../services/logService';

const defaultFilters = {
  search: '',
  username: '',
  module: '',
  action: '',
  startDate: '',
  endDate: ''
};

function AdminLogs() {
  const [auth, setAuth] = useState(!!localStorage.getItem('adminToken'));
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [filters, setFilters] = useState(defaultFilters);
  const [rows, setRows] = useState([]);
  const [usernames, setUsernames] = useState([]);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, totalPages: 1, totalCount: 0 });

  const queryParams = useMemo(
    () => ({
      ...filters,
      page: pagination.page,
      pageSize: pagination.pageSize
    }),
    [filters, pagination.page, pagination.pageSize]
  );

  useEffect(() => {
    if (!auth) return;

    const loadMeta = async () => {
      try {
        const result = await fetchFilterOptions();
        setUsernames(result.usernames || []);
        setModules(result.modules || []);
      } catch (e) {
        setError(e.message);
      }
    };

    loadMeta();
  }, [auth]);

  useEffect(() => {
    if (!auth) return;

    const loadLogs = async () => {
      setLoading(true);
      setError('');
      try {
        const result = await fetchLogs(queryParams);
        setRows(result.rows || []);
        setPagination((prev) => ({
          ...prev,
          totalPages: result.totalPages || 1,
          totalCount: result.totalCount || 0
        }));
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    loadLogs();
  }, [auth, queryParams]);

  const onLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const result = await adminLogin(credentials.username, credentials.password);
      localStorage.setItem('adminToken', result.token);
      setAuth(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const onFilter = (key, value) => {
    setPagination((p) => ({ ...p, page: 1 }));
    setFilters((f) => ({ ...f, [key]: value }));
  };

  if (!auth) {
    return (
      <div className="auth-wrap">
        <form className="card" onSubmit={onLogin}>
          <h2>Admin Logs Login</h2>
          <input
            placeholder="Username"
            value={credentials.username}
            onChange={(e) => setCredentials((v) => ({ ...v, username: e.target.value }))}
          />
          <input
            placeholder="Password"
            type="password"
            value={credentials.password}
            onChange={(e) => setCredentials((v) => ({ ...v, password: e.target.value }))}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Admin Logs Dashboard</h1>
      <p className="muted">Total Logs Count: {pagination.totalCount}</p>

      <div className="controls card">
        <input
          placeholder="Search username / module / action"
          value={filters.search}
          onChange={(e) => onFilter('search', e.target.value)}
        />
        <select value={filters.username} onChange={(e) => onFilter('username', e.target.value)}>
          <option value="">All Users</option>
          {usernames.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
        <select value={filters.module} onChange={(e) => onFilter('module', e.target.value)}>
          <option value="">All Modules</option>
          {modules.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <input placeholder="Action filter" value={filters.action} onChange={(e) => onFilter('action', e.target.value)} />
        <input type="date" value={filters.startDate} onChange={(e) => onFilter('startDate', e.target.value)} />
        <input type="date" value={filters.endDate} onChange={(e) => onFilter('endDate', e.target.value)} />

        <div className="actions">
          <button type="button" onClick={() => exportCsv(rows)}>
            Export CSV
          </button>
          <button type="button" onClick={() => downloadAllLogs(filters)}>
            Download All Logs
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <LogsTable rows={rows} loading={loading} />

      <div className="pagination">
        <button
          type="button"
          onClick={() => setPagination((p) => ({ ...p, page: Math.max(1, p.page - 1) }))}
          disabled={pagination.page === 1}
        >
          Prev
        </button>
        <span>
          Page {pagination.page} of {pagination.totalPages}
        </span>
        <button
          type="button"
          onClick={() => setPagination((p) => ({ ...p, page: Math.min(p.totalPages, p.page + 1) }))}
          disabled={pagination.page >= pagination.totalPages}
        >
          Next
        </button>

        <select
          value={pagination.pageSize}
          onChange={(e) => setPagination((p) => ({ ...p, pageSize: Number(e.target.value), page: 1 }))}
        >
          <option value={10}>10 / page</option>
          <option value={20}>20 / page</option>
        </select>
      </div>
    </div>
  );
}

export default AdminLogs;
