import React from 'react';
import { render, screen } from '@testing-library/react';
import Layout from '../src/components/Layout';

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
});

test('toggles theme and persists choice', () => {
  render(
    <Layout>
      <div>content</div>
    </Layout>
  );

  const button = screen.getByRole('button', { name: /toggle dark mode/i });
  expect(button).toHaveAttribute('aria-pressed', 'false');
  expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  expect(localStorage.getItem('theme')).toBe('light');

  button.click();

  expect(button).toHaveAttribute('aria-pressed', 'true');
  expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  expect(localStorage.getItem('theme')).toBe('dark');
});
