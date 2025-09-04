import React, { useEffect, useState } from 'react';

interface TradeRoute {
  id: number;
  source_city: string;
  dest_city: string;
  goods: string;
  quantity: number;
  tax_cents: number;
  total_cents: number;
  status: string;
}

const TradeRoutes: React.FC = () => {
  const [routes, setRoutes] = useState<TradeRoute[]>([]);

  useEffect(() => {
    const load = async () => {
      const res = await fetch('/trade/routes');
      if (res.ok) {
        const data = await res.json();
        setRoutes(data);
      }
    };
    load();
  }, []);

  return (
    <div>
      <h3 className="font-bold">Active Trade Routes</h3>
      <ul>
        {routes.map((r) => (
          <li key={r.id} className="border-b py-1">
            {r.goods} x{r.quantity} from {r.source_city} to {r.dest_city} - fee {r.tax_cents}¢ (total {r.total_cents}¢) [{r.status}]
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TradeRoutes;
