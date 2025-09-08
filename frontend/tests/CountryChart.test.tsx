import React from 'react';
import { render, screen } from '@testing-library/react';
import { CountryChart } from '../src/charts/CountryChart';

test('renders country chart rankings', async () => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () =>
        Promise.resolve([
          { position: 1, song_id: 1, band_name: 'Alpha', score: 100 },
          { position: 2, song_id: 2, band_name: 'Beta', score: 80 },
        ]),
    })
  ) as any;

  render(<CountryChart country="US" weekStart="2024-01-01" />);

  expect(await screen.findByText('1. Alpha (100)')).toBeInTheDocument();
  expect(await screen.findByText('2. Beta (80)')).toBeInTheDocument();
});
