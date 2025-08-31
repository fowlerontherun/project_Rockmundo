import React, { useEffect, useState } from 'react';

interface EventInfo {
  event_id: string;
  name: string;
  theme: string;
  description: string;
  start_date: string;
  end_date: string;
  active: boolean;
}

const emptyForm: EventInfo = {
  event_id: '',
  name: '',
  theme: '',
  description: '',
  start_date: '',
  end_date: '',
  active: false,
};

const EventsCalendar: React.FC = () => {
  const [form, setForm] = useState<EventInfo>(emptyForm);
  const [events, setEvents] = useState<EventInfo[]>([]);

  const load = async () => {
    try {
      const res = await fetch('/admin/events/upcoming');
      const data = await res.json();
      setEvents(data.upcoming || []);
    } catch {
      // ignore errors
    }
  };

  useEffect(() => {
    load();
  }, []);

  const schedule = async () => {
    await fetch('/admin/events/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: form.event_id,
        name: form.name,
        theme: form.theme,
        description: form.description,
        start_time: form.start_date,
        end_time: form.end_date,
        modifiers: {},
      }),
    });
    setForm(emptyForm);
    load();
  };

  const cancel = async (id: string) => {
    await fetch('/admin/events/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_id: id }),
    });
    load();
  };

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-4">World Events</h2>
      <div className="space-y-2 mb-6">
        <input
          className="border p-1 w-full"
          placeholder="Event ID"
          value={form.event_id}
          onChange={(e) => setForm({ ...form, event_id: e.target.value })}
        />
        <input
          className="border p-1 w-full"
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="border p-1 w-full"
          placeholder="Theme"
          value={form.theme}
          onChange={(e) => setForm({ ...form, theme: e.target.value })}
        />
        <textarea
          className="border p-1 w-full"
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
        <input
          className="border p-1 w-full"
          type="datetime-local"
          value={form.start_date}
          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
        />
        <input
          className="border p-1 w-full"
          type="datetime-local"
          value={form.end_date}
          onChange={(e) => setForm({ ...form, end_date: e.target.value })}
        />
        <button
          className="px-2 py-1 bg-green-600 text-white rounded"
          onClick={schedule}
        >
          Schedule Event
        </button>
      </div>
      <h3 className="text-lg font-semibold mb-2">Upcoming Events</h3>
      <ul className="list-disc pl-5">
        {events.map((ev) => (
          <li key={ev.event_id} className="mb-1">
            {ev.name} ({new Date(ev.start_date).toLocaleString()} -
            {new Date(ev.end_date).toLocaleString()})
            <button
              className="ml-2 px-2 py-0.5 bg-red-500 text-white rounded"
              onClick={() => cancel(ev.event_id)}
            >
              Cancel
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EventsCalendar;
