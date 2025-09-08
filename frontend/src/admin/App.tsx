import React from 'react';

import Sidebar from './components/Sidebar';
import NPCForm from './components/NPCForm';
import DialogueEditor from './npcs/DialogueEditor';
import { AuditTable } from './audit';
import { Dashboard } from './dashboard';
import { PluginManager } from './modding';
import XPEventForm from './components/XPEventForm';
import XPItemForm from './components/XPItemForm';
import { EventsCalendar } from './events';
import BooksAdmin from './learning/BooksAdmin';
import TutorialsAdmin from './learning/TutorialsAdmin';
import TutorsAdmin from './learning/TutorsAdmin';
import MentorsAdmin from './learning/MentorsAdmin';
import CityShopsAdmin from './economy/CityShopsAdmin';
import ShopAnalytics from './economy/ShopAnalytics';
import PlayerShopAdmin from './economy/PlayerShopAdmin';
import NotificationCenter from './notifications/NotificationCenter';

const App: React.FC = () => {
  const path = window.location.pathname;

  let content: React.ReactNode = (
    <>
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-gray-700">Select a module from the sidebar to begin.</p>
      <Dashboard />
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
  } else if (path.includes('/admin/economy/analytics')) {
    content = <ShopAnalytics />;
  } else if (path.includes('/admin/economy/player-shops')) {
    content = <PlayerShopAdmin />;
  } else if (path.includes('/admin/economy/city-shops')) {
    content = <CityShopsAdmin />;
  } else if (path.includes('/admin/events')) {
    content = <EventsCalendar />;
  } else if (path.includes('/admin/learning/books')) {
    content = <BooksAdmin />;
  } else if (path.includes('/admin/learning/tutorials')) {
    content = <TutorialsAdmin />;
  } else if (path.includes('/admin/learning/tutors')) {
    content = <TutorsAdmin />;
  } else if (path.includes('/admin/learning/mentors')) {
    content = <MentorsAdmin />;
  } else if (path.includes('/admin/notifications')) {
    content = <NotificationCenter />;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-4">{content}</main>
    </div>
  );
};

export default App;
