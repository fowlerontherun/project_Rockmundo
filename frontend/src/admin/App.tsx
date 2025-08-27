import React from 'react';
import Sidebar from './components/Sidebar';

const App: React.FC = () => (
  <div className="flex min-h-screen">
    <Sidebar />
    <main className="flex-1 p-4">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <p className="text-gray-700">Select a module from the sidebar to begin.</p>
    </main>
  </div>
);

export default App;
