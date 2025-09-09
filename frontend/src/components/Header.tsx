import React, { useState, useEffect, useRef } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import ThemeToggle from './ThemeToggle';
import { getToken } from '../../utils/auth.js';

declare global {
  interface Window {
    initGlobalSearch?: (el: HTMLElement) => void;
  }
}

const Header: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [user, setUser] = useState<{ username?: string; sub?: string } | null>(null);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (window.initGlobalSearch && navRef.current) {
      window.initGlobalSearch(navRef.current);
    }
    const token = getToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser(payload);
      } catch {
        // ignore parse errors
      }
    }
  }, []);

  return (
    <ThemeProvider>
      <header>
        <button className="hamburger" onClick={() => setOpen((o) => !o)}>☰</button>
        <nav ref={navRef} className={open ? 'open' : ''}>
          <a href="index.html">Home</a>
          {user ? <span className="user">{user.username || user.sub}</span> : <a href="login.html">Login</a>}
          <a href="profile.html">Profile</a>
          <ThemeToggle />
        </nav>
      </header>
    </ThemeProvider>
  );
};

export default Header;
