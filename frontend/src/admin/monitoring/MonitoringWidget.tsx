import React, { useEffect, useState } from 'react';

interface Metrics {
  cpu: number;
  memory: number;
  active_sessions: number;
}

const MonitoringWidget: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics>({ cpu: 0, memory: 0, active_sessions: 0 });
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/admin/monitoring/metrics');
        const data = await res.json();
        setMetrics(data);
      } catch {
        // swallow errors
      }
    };
    fetchMetrics();
    const id = setInterval(fetchMetrics, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const channels = ['economy', 'moderation'];
    const sockets = channels.map((c) => {
      const ws = new WebSocket(`ws://${window.location.host}/admin/realtime/ws/${c}`);
      ws.onmessage = (evt) => setAlerts((prev) => [...prev, evt.data]);
      return ws;
    });
    return () => sockets.forEach((ws) => ws.close());
  }, []);

  return (
    <div className="mt-6">
      <h2 className="text-xl font-semibold mb-2">Monitoring</h2>
      <div className="mb-4 space-y-1">
        <div>CPU: {metrics.cpu}%</div>
        <div>Memory: {metrics.memory}%</div>
        <div>Active Sessions: {metrics.active_sessions}</div>
      </div>
      <h3 className="text-lg font-semibold">Alerts</h3>
      <ul className="list-disc pl-5">
        {alerts.map((a, i) => (
          <li key={i}>{a}</li>
        ))}
      </ul>
    </div>
  );
};

export default MonitoringWidget;
