import React, { useEffect, useState } from 'react';

interface Session {
  id: string;
  user_id: number;
  ip: string;
  user_agent: string;
  created_at: string;
}

const SessionsWidget: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);

  const load = async () => {
    try {
      const res = await fetch('/admin/monitoring/sessions');
      const data = await res.json();
      setSessions(data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    load();
  }, []);

  const terminate = async (id: string) => {
    await fetch(`/admin/monitoring/sessions/${id}`, { method: 'DELETE' });
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <table className="min-w-full text-sm mb-4">
      <thead>
        <tr>
          <th className="text-left">ID</th>
          <th>User</th>
          <th>IP</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {sessions.map((s) => (
          <tr key={s.id}>
            <td>{s.id}</td>
            <td>{s.user_id}</td>
            <td>{s.ip}</td>
            <td>
              <button
                onClick={() => terminate(s.id)}
                className="text-red-600 hover:underline"
              >
                Terminate
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default SessionsWidget;
