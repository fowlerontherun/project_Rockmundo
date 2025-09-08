import React, { useState, useEffect } from 'react';

interface Schedule {
  mode: 'hourly';
  entries: Record<string, string>;
}

async function fetchSchedule(): Promise<Schedule | null> {
  try {
    const res = await fetch('/api/schedule');
    if (!res.ok) throw new Error('failed');
    return res.json();
  } catch {
    return null;
  }
}

async function saveSchedule(data: Schedule): Promise<Schedule | null> {
  try {
    const res = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('failed');
    return res.json();
  } catch {
    return null;
  }
}

const MobilePlanner: React.FC = () => {
  const [time, setTime] = useState('');
  const [value, setValue] = useState('');
  const [entries, setEntries] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchSchedule().then((sched) => {
      if (sched && sched.entries) {
        setEntries(sched.entries);
      }
    });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!time || !value) return;
    const newEntries = { ...entries, [time]: value };
    setEntries(newEntries);
    setTime('');
    setValue('');
    const payload: Schedule = { mode: 'hourly', entries: newEntries };
    await saveSchedule(payload);
  }

  return (
    <div id="mobilePlanner">
      <form onSubmit={handleSubmit}>
        <input type="time" name="time" value={time} onChange={(e) => setTime(e.target.value)} />
        <input type="text" name="value" placeholder="Activity" value={value} onChange={(e) => setValue(e.target.value)} />
        <button type="submit">Add</button>
      </form>
      <div id="mobileDisplay">
        <ul>
          {Object.keys(entries)
            .sort()
            .map((t) => (
              <li key={t}>{`${t}: ${entries[t]}`}</li>
            ))}
        </ul>
      </div>
    </div>
  );
};

export default MobilePlanner;
