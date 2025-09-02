import React, { useEffect, useState } from 'react';

interface Workshop {
  id: number;
  skill_target: string;
  xp_reward: number;
  ticket_price: number;
  schedule: string;
}

const WorkshopsAdmin: React.FC = () => {
  const [workshops, setWorkshops] = useState<Workshop[]>([]);
  const [form, setForm] = useState({
    skill_target: '',
    xp_reward: 0,
    ticket_price: 0,
    schedule: '',
  });

  const load = async () => {
    const res = await fetch('/admin/learning/workshops/');
    if (res.ok) {
      setWorkshops(await res.json());
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      skill_target: form.skill_target,
      xp_reward: Number(form.xp_reward),
      ticket_price: Number(form.ticket_price),
      schedule: form.schedule,
    };
    await fetch('/admin/learning/workshops/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    setForm({ skill_target: '', xp_reward: 0, ticket_price: 0, schedule: '' });
    load();
  };

  const handleDelete = async (id: number) => {
    await fetch(`/admin/learning/workshops/${id}`, { method: 'DELETE' });
    load();
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Workshops</h2>
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
          name="xp_reward"
          type="number"
          placeholder="XP reward"
          value={form.xp_reward}
          onChange={handleChange}
        />
        <input
          className="border p-1 w-full"
          name="ticket_price"
          type="number"
          placeholder="Ticket price"
          value={form.ticket_price}
          onChange={handleChange}
        />
        <input
          className="border p-1 w-full"
          name="schedule"
          placeholder="Schedule"
          value={form.schedule}
          onChange={handleChange}
        />
        <button type="submit" className="px-4 py-2 bg-blue-500 text-white">
          Create
        </button>
      </form>
      <ul className="space-y-1">
        {workshops.map(w => (
          <li key={w.id} className="flex justify-between items-center">
            <span>
              {w.skill_target} - {w.schedule} (${w.ticket_price})
            </span>
            <button className="text-red-600" onClick={() => handleDelete(w.id)}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default WorkshopsAdmin;
