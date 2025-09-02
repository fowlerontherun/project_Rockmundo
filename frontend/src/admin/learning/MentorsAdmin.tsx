import React, { useEffect, useState } from 'react';
import SchemaForm from '../components/SchemaForm';

interface Apprenticeship {
  id: number;
  student_id: number;
  mentor_id: number;
  mentor_type: string;
  skill_id: number;
  duration_days: number;
  level_requirement: number;
  start_date?: string | null;
  status: string;
}

const MentorsAdmin: React.FC = () => {
  const [apps, setApps] = useState<Apprenticeship[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadApps = () => {
    fetch('/admin/learning/mentors')
      .then(res => res.json())
      .then(setApps);
  };

  useEffect(() => {
    loadApps();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`/admin/learning/mentors/${id}`, { method: 'DELETE' });
    setEditingId(null);
    loadApps();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Mentors Admin</h2>
      <SchemaForm
        schemaUrl="/admin/schema/apprenticeship"
        submitUrl="/admin/learning/mentors"
        onSubmitted={loadApps}
      />
      <h3 className="text-lg mt-6 mb-2">Existing Apprenticeships</h3>
      <ul className="space-y-4">
        {apps.map(app => (
          <li key={app.id} className="border p-2">
            <div className="flex justify-between">
              <span>
                Student {app.student_id} with Mentor {app.mentor_id} ({app.status})
              </span>
              <span className="space-x-2">
                <button
                  className="text-blue-500"
                  onClick={() =>
                    setEditingId(editingId === app.id ? null : app.id)
                  }
                >
                  Edit
                </button>
                <button
                  className="text-red-500"
                  onClick={() => handleDelete(app.id)}
                >
                  Delete
                </button>
              </span>
            </div>
            {editingId === app.id && (
              <div className="mt-2">
                <SchemaForm
                  schemaUrl="/admin/schema/apprenticeship"
                  submitUrl={`/admin/learning/mentors/${app.id}`}
                  method="PUT"
                  onSubmitted={loadApps}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MentorsAdmin;
