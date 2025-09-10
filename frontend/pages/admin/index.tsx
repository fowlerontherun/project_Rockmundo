import React, { useEffect, useState } from 'react';
import AdminApp from '../../src/admin/App';
import { apiFetch } from '../../utils/api.js';

function isAuthenticated(): boolean {
  const jwt = localStorage.getItem('jwt');
  const hasSession = document.cookie.split(';').some((c) =>
    c.trim().startsWith('session=')
  );
  return Boolean(jwt || hasSession);
}

const AdminPage: React.FC = () => {
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      window.location.href = '/login';
      return;
    }

    const jwt = localStorage.getItem('jwt');

    Promise.all([
      apiFetch('/auth/permissions').then((r) => r.json()),
      apiFetch('/auth/me', {
        headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
      })
        .then((r) => (r.ok ? r.json() : { roles: [] }))
        .catch(() => ({ roles: [] })),
    ])
      .then(([available, me]) => {
        const perms: string[] = available.permissions || available || [];
        setAuthorized(perms.includes('admin') && me.roles?.includes('admin'));
      })
      .catch(() => setAuthorized(false));
  }, []);

  if (authorized === null) return null;
  return authorized ? <AdminApp /> : <div>Access denied</div>;
};

export default AdminPage;
