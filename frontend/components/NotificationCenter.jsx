const { useState, useEffect } = React;

function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);

  // initial fetch
  useEffect(() => {
    fetch('/notifications')
      .then((r) => r.json())
      .then((data) => {
        setNotifications(data.notifications || []);
        setUnread(data.unread || 0);
      })
      .catch(() => {});
  }, []);

  // websocket subscription
  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/realtime/ws`);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'notification') {
          setNotifications((prev) => [msg, ...prev]);
          setUnread((u) => u + 1);
          if (window.showNotification) {
            window.showNotification(msg.title);
          }
        }
      } catch (err) {
        // ignore
      }
    };
    return () => ws.close();
  }, []);

  function markRead(id) {
    fetch(`/notifications/${id}/read`, { method: 'POST' })
      .then(() => {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
        );
        setUnread((u) => Math.max(0, u - 1));
      })
      .catch(() => {});
  }

  return React.createElement(
    'div',
    { className: 'notification-center' },
    [
      React.createElement(
        'button',
        { key: 'bell', onClick: () => setOpen(!open) },
        `\uD83D\uDD14 ${unread}`
      ),
      open &&
        React.createElement(
          'ul',
          { key: 'list', style: { position: 'absolute', background: 'var(--surface-color)', border: '1px solid var(--border-color)', padding: '4px', listStyle: 'none' } },
          notifications.map((n) =>
            React.createElement(
              'li',
              { key: n.id, style: { marginBottom: '4px' } },
              [
                React.createElement(
                  'span',
                  { style: { fontWeight: n.read_at ? 'normal' : 'bold' } },
                  n.title
                ),
                !n.read_at &&
                  React.createElement(
                    'button',
                    { onClick: () => markRead(n.id), style: { marginLeft: '8px' } },
                    'Mark read'
                  ),
              ]
            )
          )
        ),
    ]
  );
}

document.addEventListener('DOMContentLoaded', () => {
  const rootEl = document.getElementById('notification-root');
  if (rootEl) {
    const root = ReactDOM.createRoot(rootEl);
    root.render(React.createElement(NotificationCenter));
  }
});
