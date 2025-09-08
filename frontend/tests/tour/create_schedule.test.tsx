import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import TourManager from '../../src/tour/TourManager';
import { vi } from 'vitest';

describe('tour creation and scheduling', () => {
  test('creates tour then schedules show', async () => {
    const fetchMock = vi
      .fn()
      // create tour response
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 1 }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      )
      // schedule show response
      .mockResolvedValue(
        new Response('{}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      );

    const originalFetch = global.fetch;
    vi.stubGlobal('fetch', fetchMock);

    render(<TourManager />);

    // create tour
    fireEvent.change(screen.getByPlaceholderText('Band ID'), {
      target: { value: '7' }
    });
    fireEvent.change(screen.getByPlaceholderText('Title'), {
      target: { value: 'World Domination' }
    });
    fireEvent.click(screen.getByText('Create Tour'));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tours',
        expect.objectContaining({ method: 'POST' })
      )
    );

    // schedule show
    fireEvent.change(screen.getByPlaceholderText('City'), {
      target: { value: 'New York' }
    });
    fireEvent.change(screen.getByPlaceholderText('Venue'), {
      target: { value: 'MSG' }
    });
    fireEvent.change(screen.getByPlaceholderText('Date'), {
      target: { value: '2025-01-01' }
    });
    fireEvent.click(screen.getByText('Schedule Show'));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        '/api/tours/schedule',
        expect.objectContaining({ method: 'POST' })
      )
    );

    await waitFor(() =>
      expect(screen.getByText('New York @ MSG on 2025-01-01')).toBeInTheDocument()
    );

    (globalThis as any).fetch = originalFetch;
    vi.restoreAllMocks();
  });
});

