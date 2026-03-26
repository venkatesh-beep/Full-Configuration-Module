import React, { useEffect, useMemo, useState } from 'react';
import LogsTable from '../components/LogsTable';
import { exportCsv, fetchFilterOptions, fetchLogs } from '../services/logService';

function AdminLogs() {
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  const [filters, setFilters] = useState({
    search: '',
    username: '',
    module: '',
    action: '',
    startDate: '',
    endDate: ''
  });
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [usernames, setUsernames] = useState([]);
  const [modules, setModules] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, totalPages: 1, totalCount: 0 });

  const params = useMemo(
    () => ({ ...filters, page: pagination.page, pageSize: pagination.pageSize }),
    [filters, pagination.page, pagination.pageSize]
  );

  useEffect(() => {
    if (!isAdmin) return;
    fetchFilterOptions()
      .then((res) => {
        setUsernames(res.usernames || []);
        setModules(res.modules || []);
      })
      .catch((e) => setError(e.message));
  }, [isAdmin]);

  useEffect(() => {
    if (!isAdmin) return;
    setLoading(true);
    fetchLogs(params)
      .then((res) => {
        setRows(res.rows || []);
        setPagination((prev) => ({ ...prev, totalPages: res.totalPages, totalCount: res.totalCount }));
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [isAdmin, params]);

  const onFilterChange = (key, value) => {
    setPagination((p) => ({ ...p, page: 1 }));
    setFilters((f) => ({ ...f, [key]: value }));
  };

  if (!isAdmin) {
    return (
      <div className="auth-wrap">
        <div className="card">
          <h2>Access Denied</h2>
          <p>Only the special admin user can view this route.</p>
        </div>
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
          onChange={(e) => onFilterChange('search', e.target.value)}
        />

        <select value={filters.username} onChange={(e) => onFilterChange('username', e.target.value)}>
          <option value="">All Users</option>
          {usernames.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>

        <select value={filters.module} onChange={(e) => onFilterChange('module', e.target.value)}>
          <option value="">All Modules</option>
          {modules.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <input placeholder="Filter by action" value={filters.action} onChange={(e) => onFilterChange('action', e.target.value)} />
        <input type="date" value={filters.startDate} onChange={(e) => onFilterChange('startDate', e.target.value)} />
        <input type="date" value={filters.endDate} onChange={(e) => onFilterChange('endDate', e.target.value)} />

        <button type="button" onClick={() => exportCsv(rows)}>
          Export CSV
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <LogsTable rows={rows} loading={loading} />

      <div className="pagination">
        <button type="button" disabled={pagination.page === 1} onClick={() => setPagination((p) => ({ ...p, page: p.page - 1 }))}>
          Prev
        </button>
        <span>
          Page {pagination.page} of {pagination.totalPages}
        </span>
        <button
          type="button"
          disabled={pagination.page >= pagination.totalPages}
          onClick={() => setPagination((p) => ({ ...p, page: p.page + 1 }))}
        >
          Next
        </button>

        <select value={pagination.pageSize} onChange={(e) => setPagination((p) => ({ ...p, pageSize: Number(e.target.value), page: 1 }))}>
          <option value={10}>10 / page</option>
          <option value={20}>20 / page</option>
        </select>
      </div>
    </div>
  );
}

export default AdminLogs;
