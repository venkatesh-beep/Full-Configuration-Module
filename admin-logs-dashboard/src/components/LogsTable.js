import React from 'react';

function LogsTable({ rows, loading }) {
  if (loading) {
    return <div className="spinner">Loading logs...</div>;
  }

  if (!rows.length) {
    return <div className="empty">No Data Found</div>;
  }

  const isRecent = (date) => Date.now() - new Date(date).getTime() <= 24 * 60 * 60 * 1000;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Module</th>
            <th>Action</th>
            <th>Timestamp</th>
            <th>File</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={isRecent(row.created_at) ? 'recent-row' : ''}>
              <td>{row.username || '-'}</td>
              <td>{row.module || '-'}</td>
              <td>{row.action || '-'}</td>
              <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '-'}</td>
              <td>
                {row.file_url ? (
                  <button type="button" onClick={() => window.open(row.file_url, '_blank', 'noopener,noreferrer')}>
                    Download
                  </button>
                ) : (
                  '-'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default LogsTable;
