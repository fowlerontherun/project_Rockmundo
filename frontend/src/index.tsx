import React from 'react';
import { createRoot } from 'react-dom/client';
import Header from './components/Header';
import { NotificationProvider } from './components/Notification';
import MobilePlanner from './components/MobilePlanner';

// Export components for other pages if needed
export { Header, NotificationProvider, MobilePlanner };

const container = document.getElementById('react-root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <NotificationProvider />
      <Header />
    </React.StrictMode>
  );
}

const mobile = document.getElementById('mobilePlanner');
if (mobile) {
  const mroot = createRoot(mobile);
  mroot.render(
    <React.StrictMode>
      <MobilePlanner />
    </React.StrictMode>
  );
}
