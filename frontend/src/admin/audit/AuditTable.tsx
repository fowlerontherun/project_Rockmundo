import React, { useEffect, useState } from 'react';

interface AuditLog {
  actor: number | null;
  action: string;
  resource: string;
  timestamp: string;
}

const PAGE_SIZE = 10;

const AuditTable: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(0);

  useEffect(() => {
    fetch(`/admin/audit?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`)
      .then((res) => res.json())
      .then((data) => setLogs(Array.isArray(data) ? data : []))
      .catch(() => setLogs([]));
  }, [page]);

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Audit Logs</h2>
      <table className="min-w-full border">
        <thead>
          <tr>
            <th className="border px-2">Actor</th>
            <th className="border px-2">Action</th>
            <th className="border px-2">Resource</th>
            <th className="border px-2">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log, idx) => (
            <tr key={idx}>
              <td className="border px-2">{log.actor}</td>
              <td className="border px-2">{log.action}</td>
              <td className="border px-2">{log.resource}</td>
              <td className="border px-2">{log.timestamp}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-2 flex gap-2">
        <button
          className="px-2 py-1 border"
          disabled={page === 0}
          onClick={() => setPage((p) => Math.max(0, p - 1))}
        >
          Prev
        </button>
        <button
          className="px-2 py-1 border"
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default AuditTable;
