import React from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import ThemeToggle from './ThemeToggle';

const Navigation: React.FC = () => (
  <nav className="bg-[var(--bg-color)] border-t md:border-t-0 md:border-r border-gray-200">
    <ul className="flex justify-around md:flex-col md:justify-start p-4 gap-4">
      <li><a href="#" className="hover:text-[var(--accent-color)]">Home</a></li>
      <li><a href="#" className="hover:text-[var(--accent-color)]">About</a></li>
    </ul>
  </nav>
);

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <div className="min-h-screen grid grid-rows-[auto_1fr] bg-[var(--bg-color)] text-[var(--text-color)]">
      <header className="flex items-center justify-between p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold">Rockmundo</h1>
        <ThemeToggle />
      </header>
      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] lg:grid-cols-[250px_1fr] flex-1">
        <Navigation />
        <main className="p-4">{children}</main>
      </div>
    </div>
  </ThemeProvider>
);

export default Layout;

