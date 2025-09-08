import React, { useEffect, useMemo, useState } from 'react';
import {
  Calendar,
  dateFnsLocalizer,
  Event as RBCEvent,
} from 'react-big-calendar';
import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop';
import format from 'date-fns/format';
import parse from 'date-fns/parse';
import startOfWeek from 'date-fns/startOfWeek';
import getDay from 'date-fns/getDay';
import enUS from 'date-fns/locale/en-US';
import 'react-big-calendar/lib/addons/dragAndDrop/styles.css';
import 'react-big-calendar/lib/css/react-big-calendar.css';

interface EventInfo {
  event_id: string;
  name: string;
  theme: string;
  description: string;
  start_date: string;
  end_date: string;
  active: boolean;
  timezone?: string;
}

const emptyForm: EventInfo = {
  event_id: '',
  name: '',
  theme: '',
  description: '',
  start_date: '',
  end_date: '',
  active: false,
  timezone: 'UTC',
};

const locales = { 'en-US': enUS };
const localizer = dateFnsLocalizer({ format, parse, startOfWeek, getDay, locales });
const DragAndDropCalendar = withDragAndDrop(Calendar);

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
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    await fetch('/admin/events/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: form.event_id,
        name: form.name,
        theme: form.theme,
        description: form.description,
        start_time: new Date(form.start_date).toISOString(),
        end_time: new Date(form.end_date).toISOString(),
        timezone: tz,
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

  const onMove = async ({ event, start, end }: any) => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    await fetch('/admin/events/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: (event as EventInfo).event_id,
        start_time_utc: start.toISOString(),
        end_time_utc: end.toISOString(),
        timezone: tz,
      }),
    });
    load();
  };

  const calendarEvents = useMemo<RBCEvent<EventInfo>[]>(
    () =>
      events.map((ev) => ({
        ...ev,
        title: ev.name,
        start: new Date(ev.start_date),
        end: new Date(ev.end_date),
      })),
    [events]
  );

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
      <div className="h-96">
        <DragAndDropCalendar
          localizer={localizer}
          events={calendarEvents}
          startAccessor="start"
          endAccessor="end"
          onEventDrop={onMove}
          onEventResize={onMove}
          resizable
        />
      </div>
      <ul className="list-disc pl-5 mt-4">
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
