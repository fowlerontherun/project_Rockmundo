import React from 'react';
import { useTheme } from '../context/ThemeContext';
const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  return (
    <button onClick={toggleTheme} aria-pressed={theme === 'dark'}>
      {theme === 'dark' ? '🌞' : '🌙'}
  const isDark = theme === 'dark';
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      className="p-2 rounded text-[var(--text-color)] hover:bg-[var(--accent-color)] hover:text-[var(--bg-color)] focus:bg-[var(--accent-color)] focus:text-[var(--bg-color)] focus:outline-none"
    >
      <span className="sr-only">Toggle dark mode</span>
      <span aria-hidden="true">{isDark ? '🌙' : '☀️'}</span>
    </button>
  );
};

export default ThemeToggle;