import React from 'react';

import Sidebar from './components/Sidebar';
import NPCForm from './components/NPCForm';
import DialogueEditor from './npcs/DialogueEditor';
import { AuditTable } from './audit';
import { MonitoringWidget } from './monitoring';
import { PluginManager } from './modding';
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

  if (path.includes('/admin/npcs/dialogue')) {
    content = <DialogueEditor />;
  } else if (path.includes('/admin/npcs')) {
    content = <NPCForm />;
  } else if (path.includes('/admin/audit')) {
    content = <AuditTable />;
  } else if (path.includes('/admin/xp-events')) {
    content = <XPEventForm />;
  } else if (path.includes('/admin/xp-items')) {
    content = <XPItemForm />;
  } else if (path.includes('/admin/modding')) {
    content = <PluginManager />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-4">{content}</main>
    </div>
  );
};

export default App;
