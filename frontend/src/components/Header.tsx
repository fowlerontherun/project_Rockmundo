import React, { useState, useEffect, useRef } from 'react';

declare global {
  interface Window {
    initGlobalSearch?: (el: HTMLElement) => void;
  }
}

const Header: React.FC = () => {
  const [open, setOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (window.initGlobalSearch && navRef.current) {
      window.initGlobalSearch(navRef.current);
    }
  }, []);

  return (
    <header>
      <button className="hamburger" onClick={() => setOpen((o) => !o)}>☰</button>
      <nav ref={navRef} className={open ? 'open' : ''}>
        <a href="index.html">Home</a>
        <a href="profile.html">Profile</a>
      </nav>
    </header>
  );
};

export default Header;
