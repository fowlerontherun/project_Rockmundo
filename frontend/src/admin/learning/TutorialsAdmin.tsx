import React, { useEffect, useState } from 'react';
import SchemaForm from '../components/SchemaForm';

interface OnlineTutorial {
  id: number;
  video_url: string;
  skill: string;
  xp_rate: number;
  plateau_level: number;
  rarity_weight: number;
}

const TutorialsAdmin: React.FC = () => {
  const [tutorials, setTutorials] = useState<OnlineTutorial[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadTutorials = () => {
    fetch('/admin/learning/tutorials')
      .then(res => res.json())
      .then(setTutorials);
  };

  useEffect(() => {
    loadTutorials();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`/admin/learning/tutorials/${id}`, { method: 'DELETE' });
    setEditingId(null);
    loadTutorials();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Online Tutorials Admin</h2>
      <SchemaForm
        schemaUrl="/admin/schema/online_tutorial"
        submitUrl="/admin/learning/tutorials"
        onSubmitted={loadTutorials}
      />
      <h3 className="text-lg mt-6 mb-2">Existing Tutorials</h3>
      <ul className="space-y-4">
        {tutorials.map(tutorial => (
          <li key={tutorial.id} className="border p-2">
            <div className="flex justify-between">
              <span>
                {tutorial.skill} - {tutorial.video_url}
              </span>
              <span className="space-x-2">
                <button
                  className="text-blue-500"
                  onClick={() =>
                    setEditingId(editingId === tutorial.id ? null : tutorial.id)
                  }
                >
                  Edit
                </button>
                <button
                  className="text-red-500"
                  onClick={() => handleDelete(tutorial.id)}
                >
                  Delete
                </button>
              </span>
            </div>
            {editingId === tutorial.id && (
              <div className="mt-2">
                <SchemaForm
                  schemaUrl="/admin/schema/online_tutorial"
                  submitUrl={`/admin/learning/tutorials/${tutorial.id}`}
                  method="PUT"
                  onSubmitted={loadTutorials}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TutorialsAdmin;
