import React, { useEffect, useState } from 'react';

type Notification = {
  id: number;
  message: string;
  severity: string;
  created_at: string;
  read: number;
};

const groupBy = (items: Notification[]) => {
  return items.reduce<Record<string, Notification[]>>((acc, item) => {
    acc[item.severity] = acc[item.severity] || [];
    acc[item.severity].push(item);
    return acc;
  }, {});
};

const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const refresh = () => {
    fetch('/admin/notifications')
      .then((r) => r.json())
      .then((data) => {
        setNotifications(data.notifications || []);
        if ((window as any).setAdminNotifCount) {
          (window as any).setAdminNotifCount(data.unread || 0);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    refresh();
  }, []);

  const markRead = (id: number) => {
    fetch(`/admin/notifications/${id}/read`, { method: 'POST' })
      .then(() => {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, read: 1 } : n))
        );
        if ((window as any).setAdminNotifCount) {
          const unread = notifications.filter((n) => !n.read && n.id !== id).length;
          (window as any).setAdminNotifCount(unread);
        }
      })
      .catch(() => {});
  };

  const groups = groupBy(notifications);

  return (
    <div>
      {Object.entries(groups).map(([severity, items]) => (
        <div key={severity} className="mb-4">
          <h2 className="font-bold capitalize">
            {severity} ({items.filter((i) => !i.read).length}/{items.length})
          </h2>
          <ul className="ml-4 list-disc">
            {items.map((n) => (
              <li key={n.id} className="mb-1">
                <span className={n.read ? 'text-gray-600' : 'font-semibold'}>
                  {n.message}
                </span>
                {!n.read && (
                  <button
                    onClick={() => markRead(n.id)}
                    className="ml-2 text-sm text-blue-500"
                  >
                    Mark read
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
};

export default NotificationCenter;
