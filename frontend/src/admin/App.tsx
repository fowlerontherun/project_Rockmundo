import React from 'react';

import Sidebar from './components/Sidebar';
import { AuditTable } from './audit';
import { MonitoringWidget } from './monitoring';
import XPEventForm from './components/XPEventForm';
import XPItemForm from './components/XPItemForm';

const App: React.FC = () => {
  const path = window.location.pathname;

  let content: React.ReactNode = (
    <>
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-gray-700">Select a module from the sidebar to begin.</p>
      <MonitoringWidget />
    </>
  );

  if (path.includes('/admin/audit')) {
    content = <AuditTable />;
  } else if (path.includes('/admin/xp-events')) {
    content = <XPEventForm />;
  } else if (path.includes('/admin/xp-items')) {
    content = <XPItemForm />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-4">{content}</main>
    </div>
  );
};

export default App;
