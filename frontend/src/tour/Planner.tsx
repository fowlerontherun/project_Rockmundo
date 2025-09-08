import React, { useEffect, useRef, useState } from 'react';

// simple event bus so updateSlot can notify planner instances
const plannerBus = new EventTarget();

export async function fetchSchedule(): Promise<Record<string, any>> {
  const res = await fetch('/api/tours/planner/schedule');
  if (!res.ok) {
    throw new Error('Failed to fetch schedule');
  }
  return res.json();
}

export async function saveSlot(time: string, value: any, durationDays = 1) {
  const res = await fetch(`/api/tours/planner/schedule/${encodeURIComponent(time)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, durationDays })
  });
  if (!res.ok) {
    throw new Error('Failed to save slot');
  }
  return res.json();
}

export async function deleteSlot(time: string) {
  const res = await fetch(`/api/tours/planner/schedule/${encodeURIComponent(time)}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    throw new Error('Failed to delete slot');
  }
  return res.json();
}

export async function updateSlot(time: string, value: any, durationDays = 1) {
  plannerBus.dispatchEvent(
    new CustomEvent('planner-update', { detail: { time, value } })
  );
  return saveSlot(time, value, durationDays);
}

interface ScheduleItem {
  date: string;
  venue: string;
}

interface ExpenseItem {
  description: string;
  amount: number;
}

export const Planner: React.FC = () => {
  const [entries, setEntries] = useState<Record<string, any>>({});
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [expenses, setExpenses] = useState<ExpenseItem[]>([]);
  const gridRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      const { time, value } = (e as CustomEvent<{ time: string; value: any }>).detail;
      setEntries((prev) => ({ ...prev, [time]: value }));
    };
    plannerBus.addEventListener('planner-update', handler);
    fetchSchedule().then(setEntries).catch(() => {});
    return () => {
      plannerBus.removeEventListener('planner-update', handler);
    };
  }, []);

  const handleAddDate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const date = (form.elements.namedItem('date') as HTMLInputElement).value;
    const venue = (form.elements.namedItem('venue') as HTMLInputElement).value;
    const item = { date, venue };
    await fetch('/api/tours/planner/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    setSchedule((prev) => [...prev, item]);
    form.reset();
  };

  const handleDeleteDate = async (idx: number) => {
    const item = schedule[idx];
    await fetch('/api/tours/planner/schedule', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    setSchedule((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAddExpense = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const description = (form.elements.namedItem('description') as HTMLInputElement).value;
    const amount = parseFloat((form.elements.namedItem('amount') as HTMLInputElement).value);
    const item = { description, amount };
    await fetch('/api/tours/planner/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    setExpenses((prev) => [...prev, item]);
    form.reset();
  };

  const handleDeleteExpense = async (idx: number) => {
    const item = expenses[idx];
    await fetch('/api/tours/planner/expenses', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    setExpenses((prev) => prev.filter((_, i) => i !== idx));
  };

  const slots = [] as JSX.Element[];
  for (let h = 0; h < 24; h++) {
    for (let q = 0; q < 4; q++) {
      const minutes = q * 15;
      const time = `${String(h).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
      const d = new Date();
      d.setHours(h, minutes, 0, 0);
      const label = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const content = entries[time]
        ? typeof entries[time] === 'object'
          ? entries[time].label || entries[time].value || ''
          : entries[time]
        : label;
      slots.push(
        <div
          key={time}
          className="slot"
          data-time={time}
          draggable
          onDragStart={(e) => e.dataTransfer.setData('text/plain', time)}
          onDrop={(e) => {
            e.preventDefault();
            const src = e.dataTransfer.getData('text/plain');
            if (src && entries[src]) {
              updateSlot(time, entries[src]);
            }
          }}
          onDragOver={(e) => e.preventDefault()}
          style={{ border: '1px solid var(--border-color)', padding: '2px', minHeight: '20px' }}
        >
          {content}
        </div>
      );
    }
  }

  return (
    <div>
      <div
        id="plannerGrid"
        ref={gridRef}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: '2px' }}
      >
        {slots}
      </div>

      <h3>Tour Dates</h3>
      <form onSubmit={handleAddDate}>
        <input name="date" placeholder="Date" required />
        <input name="venue" placeholder="Venue" required />
        <button type="submit">Add Date</button>
      </form>
      <ul>
        {schedule.map((s, i) => (
          <li key={`${s.date}-${i}`}>{`${s.date} @ ${s.venue}`}
            <button onClick={() => handleDeleteDate(i)}>Delete</button>
          </li>
        ))}
      </ul>

      <h3>Expenses</h3>
      <form onSubmit={handleAddExpense}>
        <input name="description" placeholder="Description" required />
        <input name="amount" type="number" step="0.01" placeholder="Amount" required />
        <button type="submit">Add Expense</button>
      </form>
      <ul>
        {expenses.map((e, i) => (
          <li key={`${e.description}-${i}`}>{`${e.description}: $${e.amount}`}
            <button onClick={() => handleDeleteExpense(i)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Planner;
