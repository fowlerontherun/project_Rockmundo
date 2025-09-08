import React from 'react';
import { render, screen } from '@testing-library/react';
import { MetricsWidget } from '../src/admin/dashboard';

global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ cpu: 10, memory: 20, active_sessions: 5 }),
  })
) as any;

test('renders metrics from API', async () => {
  render(<MetricsWidget />);
  expect(await screen.findByText(/CPU: 10%/)).toBeInTheDocument();
  expect(await screen.findByText(/Memory: 20%/)).toBeInTheDocument();
  expect(await screen.findByText(/Active Sessions: 5/)).toBeInTheDocument();
});
