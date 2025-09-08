import React, { useEffect, useState } from 'react';

interface Entry {
  position: number;
  song_id: number;
  band_name: string;
  score: number;
}

interface Props {
  country: string;
  weekStart: string;
}

/**
 * Display ranking entries for a given country.
 */
export function CountryChart({ country, weekStart }: Props) {
  const [entries, setEntries] = useState<Entry[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch(`/charts/country/${country}/${weekStart}`)
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setEntries(data);
      });
    return () => {
      cancelled = true;
    };
  }, [country, weekStart]);

  return (
    <ol>
      {entries.map((e) => (
        <li key={e.position}>
          {e.position}. {e.band_name} ({e.score})
        </li>
      ))}
    </ol>
  );
}
