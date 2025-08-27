import React from 'react';
import Sidebar from './components/Sidebar';
import { AuditTable } from './audit';

const App: React.FC = () => {
  const path = window.location.pathname;
  let content: React.ReactNode = (
    <>
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-gray-700">Select a module from the sidebar to begin.</p>
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

export default App;
