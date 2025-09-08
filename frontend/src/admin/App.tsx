import React from 'react';
import { Routes, Route } from 'react-router-dom';

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

const DashboardHome = () => (
  <>
    <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
    <p className="text-gray-700">Select a module from the sidebar to begin.</p>
    <Dashboard />
  </>
);

const App: React.FC = () => (
  <div className="flex min-h-screen">
    <Sidebar />
    <main className="flex-1 p-4">
      <Routes>
        <Route path="/admin/npcs/dialogue" element={<DialogueEditor />} />
        <Route path="/admin/npcs" element={<NPCForm />} />
        <Route path="/admin/audit" element={<AuditTable />} />
        <Route path="/admin/xp-events" element={<XPEventForm />} />
        <Route path="/admin/xp-items" element={<XPItemForm />} />
        <Route path="/admin/modding" element={<PluginManager />} />
        <Route path="/admin/economy/analytics" element={<ShopAnalytics />} />
        <Route path="/admin/economy/player-shops" element={<PlayerShopAdmin />} />
        <Route path="/admin/economy/city-shops" element={<CityShopsAdmin />} />
        <Route path="/admin/events" element={<EventsCalendar />} />
        <Route path="/admin/learning/books" element={<BooksAdmin />} />
        <Route path="/admin/learning/tutorials" element={<TutorialsAdmin />} />
        <Route path="/admin/learning/tutors" element={<TutorsAdmin />} />
        <Route path="/admin/learning/mentors" element={<MentorsAdmin />} />
        <Route path="/dashboard" element={<DashboardHome />} />
        <Route path="*" element={<DashboardHome />} />
      </Routes>
    </main>
  </div>
);

export default App;
