import React from 'react';
import { render, screen } from '@testing-library/react';
import { Dashboard } from '../src/admin/dashboard';

global.fetch = jest.fn((url: string) => {
  if (url.includes('/api/daily/status')) {
    return Promise.resolve({
      json: () =>
        Promise.resolve({
          login_streak: 5,
          current_challenge: 'Practice scales',
          reward_claimed: false,
          next_weekly_reward: { drop_date: '2023-01-01', reward: 'bronze' },
        }),
    });
  }
  return Promise.resolve({
    json: () => Promise.resolve({ cpu: 10, memory: 20, active_sessions: 5 }),
  });
}) as any;

test('renders dashboard with metrics and daily loop', async () => {
  render(<Dashboard />);
  expect(await screen.findByText(/CPU: 10%/)).toBeInTheDocument();
  expect(await screen.findByText(/Streak: 5/)).toBeInTheDocument();
  expect(await screen.findByText(/Challenge: Practice scales/)).toBeInTheDocument();
});
