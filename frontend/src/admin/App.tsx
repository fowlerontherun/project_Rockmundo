import React from 'react';
import Sidebar from './components/Sidebar';
codex/expose-monitoring-metrics-in-backend
import { MonitoringWidget } from './monitoring';

const App: React.FC = () => {
  const path = window.location.pathname;
  let content: React.ReactNode = (
    <>
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-gray-700">Select a module from the sidebar to begin.</p>
codex/expose-monitoring-metrics-in-backend
      <MonitoringWidget />
    </main>
  </div>
);
=======
    </>
  );

  if (path.includes('/admin/audit')) {
    content = <AuditTable />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-4">{content}</main>
    </div>
  );
};

