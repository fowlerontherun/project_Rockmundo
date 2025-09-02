import React, { useEffect, useState } from 'react';

interface Course {
  id: number;
  skill_target: string;
  duration: number;
  prerequisites?: Record<string, any> | null;
  prestige: boolean;
}

const CoursesAdmin: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [form, setForm] = useState({
    skill_target: '',
    duration: 0,
    prerequisites: '',
    prestige: false,
  });

  const load = async () => {
    const res = await fetch('/admin/courses/');
    if (res.ok) {
      setCourses(await res.json());
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      skill_target: form.skill_target,
      duration: Number(form.duration),
      prerequisites: form.prerequisites ? JSON.parse(form.prerequisites) : null,
      prestige: form.prestige,
    };
    await fetch('/admin/courses/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    setForm({ skill_target: '', duration: 0, prerequisites: '', prestige: false });
    load();
  };

  const handleDelete = async (id: number) => {
    await fetch(`/admin/courses/${id}`, { method: 'DELETE' });
    load();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Courses</h2>
      <form onSubmit={handleCreate} className="space-y-2 mb-4">
        <input
          className="border p-1 w-full"
          name="skill_target"
          placeholder="Skill target"
          value={form.skill_target}
          onChange={handleChange}
        />
        <input
          className="border p-1 w-full"
          name="duration"
          type="number"
          placeholder="Duration"
          value={form.duration}
          onChange={handleChange}
        />
        <input
          className="border p-1 w-full"
          name="prerequisites"
          placeholder='Prerequisites JSON'
          value={form.prerequisites}
          onChange={handleChange}
        />
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            name="prestige"
            checked={form.prestige}
            onChange={handleChange}
          />
          <span>Prestige</span>
        </label>
        <button type="submit" className="px-4 py-2 bg-blue-500 text-white">
          Create
        </button>
      </form>
      <ul className="space-y-1">
        {courses.map(c => (
          <li key={c.id} className="flex justify-between items-center">
            <span>
              {c.skill_target} - {c.duration}w {c.prestige ? '(Prestige)' : ''}
            </span>
            <button
              className="text-red-600"
              onClick={() => handleDelete(c.id)}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CoursesAdmin;
