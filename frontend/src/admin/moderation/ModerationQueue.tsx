import React, { useEffect, useState } from 'react';

interface Submission {
  id: number;
  name: string;
  status: string;
}

const ModerationQueue: React.FC = () => {
  const [queue, setQueue] = useState<Submission[]>([]);

  const load = async () => {
    try {
      const res = await fetch('/admin/media/queue');
      const data = await res.json();
      setQueue(data);
    } catch {
      // ignore errors for now
    }
  };

  useEffect(() => {
    load();
  }, []);

  const review = async (id: number, decision: 'approve' | 'reject') => {
    await fetch(`/admin/media/review/${id}/${decision}`, { method: 'POST' });
    load();
  };

  if (queue.length === 0) {
    return <div>No submissions</div>;
  }

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-4">Pending Skins</h2>
      <ul>
        {queue.map((s) => (
          <li key={s.id} className="flex items-center justify-between mb-2">
            <span>{s.name}</span>
            <div>
              <button
                className="px-2 py-1 bg-green-500 text-white rounded mr-2"
                onClick={() => review(s.id, 'approve')}
              >
                Approve
              </button>
              <button
                className="px-2 py-1 bg-red-500 text-white rounded"
                onClick={() => review(s.id, 'reject')}
              >
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ModerationQueue;

