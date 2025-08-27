import React, { useEffect, useState } from 'react';
import AdminApp from '../../src/admin/App';

function isAuthenticated(): boolean {
  const jwt = localStorage.getItem('jwt');
  const hasSession = document.cookie.split(';').some((c) =>
    c.trim().startsWith('session=')
  );
  return Boolean(jwt || hasSession);
}

const AdminPage: React.FC = () => {
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      setAuthorized(true);
    } else {
      window.location.href = '/login';
    }
  }, []);

  return authorized ? <AdminApp /> : null;
};

export default AdminPage;
