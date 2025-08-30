import React from 'react';
import { render, screen } from '@testing-library/react';
import MonitoringWidget from '../src/admin/monitoring/MonitoringWidget';

test('renders metrics from API', async () => {
  render(<MonitoringWidget />);
  expect(await screen.findByText(/CPU: 10%/)).toBeInTheDocument();
  expect(await screen.findByText(/Memory: 20%/)).toBeInTheDocument();
  expect(await screen.findByText(/Active Sessions: 5/)).toBeInTheDocument();
});
