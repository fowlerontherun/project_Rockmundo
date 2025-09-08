import React, { useEffect, useState } from 'react';

const AlertsWidget: React.FC = () => {
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/admin/realtime/ws`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ op: 'subscribe', topics: ['economy', 'moderation'] }));
    };
    ws.onmessage = (evt) => setAlerts((prev) => [...prev, evt.data]);
    return () => ws.close();
  }, []);

  return (
    <ul className="list-disc pl-5">
      {alerts.map((a, i) => (
        <li key={i}>{a}</li>
      ))}
    </ul>
  );
};

export default AlertsWidget;
