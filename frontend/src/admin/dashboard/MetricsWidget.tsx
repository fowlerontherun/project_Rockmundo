import React, { useEffect, useState } from 'react';

interface Metrics {
  cpu: number;
  memory: number;
  active_sessions: number;
}

const MetricsWidget: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics>({ cpu: 0, memory: 0, active_sessions: 0 });

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('/admin/monitoring/metrics');
        const data = await res.json();
        setMetrics(data);
      } catch {
        // ignore
      }
    };
    fetchMetrics();
    const id = setInterval(fetchMetrics, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mb-4 space-y-1">
      <div>CPU: {metrics.cpu}%</div>
      <div>Memory: {metrics.memory}%</div>
      <div>Active Sessions: {metrics.active_sessions}</div>
    </div>
  );
};

export default MetricsWidget;
