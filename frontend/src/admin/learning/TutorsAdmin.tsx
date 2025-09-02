import React, { useEffect, useState } from 'react';
import SchemaForm from '../components/SchemaForm';

interface Tutor {
  id: number;
  name: string;
  specialization: string;
  hourly_rate: number;
  level_requirement: number;
}

const TutorsAdmin: React.FC = () => {
  const [tutors, setTutors] = useState<Tutor[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);

  const loadTutors = () => {
    fetch('/admin/learning/tutors')
      .then(res => res.json())
      .then(setTutors);
  };

  useEffect(() => {
    loadTutors();
  }, []);

  const handleDelete = async (id: number) => {
    await fetch(`/admin/learning/tutors/${id}`, { method: 'DELETE' });
    setEditingId(null);
    loadTutors();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Tutors Admin</h2>
      <SchemaForm
        schemaUrl="/admin/schema/tutor"
        submitUrl="/admin/learning/tutors"
        onSubmitted={loadTutors}
      />
      <h3 className="text-lg mt-6 mb-2">Existing Tutors</h3>
      <ul className="space-y-4">
        {tutors.map(tutor => (
          <li key={tutor.id} className="border p-2">
            <div className="flex justify-between">
              <span>
                {tutor.name} - {tutor.specialization} (${tutor.hourly_rate}/hr)
              </span>
              <span className="space-x-2">
                <button
                  className="text-blue-500"
                  onClick={() =>
                    setEditingId(editingId === tutor.id ? null : tutor.id)
                  }
                >
                  Edit
                </button>
                <button
                  className="text-red-500"
                  onClick={() => handleDelete(tutor.id)}
                >
                  Delete
                </button>
              </span>
            </div>
            {editingId === tutor.id && (
              <div className="mt-2">
                <SchemaForm
                  schemaUrl="/admin/schema/tutor"
                  submitUrl={`/admin/learning/tutors/${tutor.id}`}
                  method="PUT"
                  onSubmitted={loadTutors}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TutorsAdmin;
