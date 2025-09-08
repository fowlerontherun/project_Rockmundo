import React, { useState } from 'react';

interface ShowItem {
  city: string;
  venue: string;
  date: string;
}

/**
 * Simple component that lets a user create a tour and then schedule shows for
 * it.  This is intentionally lightweight – the backend endpoints are mocked in
 * tests so the component only needs to issue fetch calls.
 */
const TourManager: React.FC = () => {
  const [tourId, setTourId] = useState<number | null>(null);
  const [shows, setShows] = useState<ShowItem[]>([]);

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const bandId = parseInt((form.elements.namedItem('bandId') as HTMLInputElement).value, 10);
    const title = (form.elements.namedItem('title') as HTMLInputElement).value;

    const res = await fetch('/api/tours', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ band_id: bandId, title })
    });
    const data = await res.json();
    setTourId(data.id);
    form.reset();
  };

  const handleSchedule = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const city = (form.elements.namedItem('city') as HTMLInputElement).value;
    const venue = (form.elements.namedItem('venue') as HTMLInputElement).value;
    const date = (form.elements.namedItem('date') as HTMLInputElement).value;

    await fetch('/api/tours/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tour_id: tourId,
        city,
        venue,
        date,
        ticket_tiers: [],
        expenses: []
      })
    });

    setShows((prev) => [...prev, { city, venue, date }]);
    form.reset();
  };

  return (
    <div>
      <form onSubmit={handleCreate}>
        <input name="bandId" placeholder="Band ID" required />
        <input name="title" placeholder="Title" required />
        <button type="submit">Create Tour</button>
      </form>

      {tourId && (
        <form onSubmit={handleSchedule}>
          <input name="city" placeholder="City" required />
          <input name="venue" placeholder="Venue" required />
          <input name="date" placeholder="Date" required />
          <button type="submit">Schedule Show</button>
        </form>
      )}

      <ul>
        {shows.map((s, i) => (
          <li key={`${s.city}-${s.venue}-${i}`}>{`${s.city} @ ${s.venue} on ${s.date}`}</li>
        ))}
      </ul>
    </div>
  );
};

export default TourManager;

