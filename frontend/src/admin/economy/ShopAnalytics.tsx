import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface TopItem {
  sku_id: number;
  units: number;
  revenue_cents: number;
}

interface ShopMetrics {
  orders: number;
  revenue_cents: number;
  top_items: TopItem[];
}

const ShopAnalytics: React.FC = () => {
  const [metrics, setMetrics] = useState<ShopMetrics | null>(null);

  useEffect(() => {
    fetch('/admin/economy/analytics')
      .then((res) => res.json())
      .then(setMetrics)
      .catch(() => setMetrics(null));
  }, []);

  if (!metrics) {
    return <div>Loading...</div>;
  }

  const chartData = {
    labels: metrics.top_items.map((i) => `SKU ${i.sku_id}`),
    datasets: [
      {
        label: 'Units Sold',
        data: metrics.top_items.map((i) => i.units),
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
      },
    ],
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Shop Analytics</h2>
      <div className="mb-2">Total Orders: {metrics.orders}</div>
      <div className="mb-4">
        Total Revenue: ${(metrics.revenue_cents / 100).toFixed(2)}
      </div>
      <Bar data={chartData} />
    </div>
  );
};

export default ShopAnalytics;

