import React from 'react';
import { createRoot } from 'react-dom/client';
import Header from './components/Header';
import { NotificationProvider } from './components/Notification';
import MobilePlanner from './components/MobilePlanner';
import { ThemeProvider } from './context/ThemeContext';
import ThemeToggle from './components/ThemeToggle';

// Export components for other pages if needed
export { Header, NotificationProvider, MobilePlanner };

const container = document.getElementById('react-root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <ThemeProvider>
        <NotificationProvider />
        <ThemeToggle />
        <Header />
      </ThemeProvider>
    </React.StrictMode>
  );
}

const mobile = document.getElementById('mobilePlanner');
if (mobile) {
  const mroot = createRoot(mobile);
  mroot.render(
    <React.StrictMode>
      <ThemeProvider>
        <MobilePlanner />
      </ThemeProvider>
    </React.StrictMode>
  );
}
