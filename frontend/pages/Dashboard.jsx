import React, { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

function isAuthenticated() {
  const jwt = localStorage.getItem('jwt');
  const hasSession = document.cookie
    .split(';')
    .some((c) => c.trim().startsWith('session='));
  return Boolean(jwt || hasSession);
}

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      window.location.href = '/login';
      return;
    }

    fetch('/dashboard/summary')
      .then((res) => {
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        return res.json();
      })
      .then((data) => setSummary(data))
      .catch(() => setError(true));
  }, []);

  if (error) {
    return <div className="p-4 text-red-500">Unable to load dashboard.</div>;
  }

  if (!summary) {
    return <div className="p-4">Loading...</div>;
  }

  const topSongsData = {
    labels: summary.topSongs.map((s) => s.title),
    datasets: [
      {
        label: 'Plays',
        data: summary.topSongs.map((s) => s.plays),
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
    ],
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Dashboard</h1>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="bg-white rounded shadow p-4">
          <h2 className="text-xl mb-2">Top Songs</h2>
          <Bar data={topSongsData} />
        </div>
        <div className="bg-white rounded shadow p-4">
          <h2 className="text-xl mb-2">Current Gigs</h2>
          <ul>
            {summary.currentGigs.map((gig, idx) => (
              <li key={idx}>
                {gig.venue} - {gig.date}
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded shadow p-4 md:col-span-2">
          <h2 className="text-xl mb-2">Financials</h2>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <p>Revenue: ${summary.financials.revenue}</p>
              <p>Expenses: ${summary.financials.expenses}</p>
              <p>Profit: ${summary.financials.profit}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
