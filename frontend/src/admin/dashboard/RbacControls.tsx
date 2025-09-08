import React, { useEffect, useState } from 'react';

const RbacControls: React.FC = () => {
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/admin/monitoring/permissions');
        const data = await res.json();
        setAllowed(Boolean(data.allowed));
      } catch {
        setAllowed(false);
      }
    };
    check();
  }, []);

  if (!allowed) return null;

  return (
    <button className="mt-4 px-4 py-2 bg-blue-500 text-white rounded" disabled={!allowed}>
      Restricted Action
    </button>
  );
};

export default RbacControls;
