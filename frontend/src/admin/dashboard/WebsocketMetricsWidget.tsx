import React, { useEffect, useState } from 'react';

interface Stats {
  connections: number;
  messages: number;
}

const WebsocketMetricsWidget: React.FC = () => {
  const [stats, setStats] = useState<Stats>({ connections: 0, messages: 0 });

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/realtime/ws`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ op: 'subscribe', topics: ['metrics'] }));
    };
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.data && typeof msg.data.connections === 'number') {
          setStats(msg.data);
        }
      } catch {
        // ignore parse errors
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div className="mb-4 space-y-1">
      <div>Connections: {stats.connections}</div>
      <div>Messages: {stats.messages}</div>
    </div>
  );
};

export default WebsocketMetricsWidget;
