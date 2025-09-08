import { render, screen, waitFor } from '@testing-library/react';
import { Planner, updateSlot } from '../../src/tour/Planner';
import sched from '../schedule/fixtures/schedule.json';
import { vi } from 'vitest';

describe('tour planner', () => {
  test('renders grid and updates slot', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(sched), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValue(
        new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } })
      );

    const originalFetch = global.fetch;
    vi.stubGlobal('fetch', fetchMock);

    render(<Planner />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());

    const slots = document.querySelectorAll('#plannerGrid .slot');
    expect(slots.length).toBe(96);
    expect(await screen.findByText('Sleep')).toBeInTheDocument();

    await updateSlot('00:15', 'Practice');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/tour-collab/schedule/00:15',
      expect.objectContaining({ method: 'PUT' })
    );
    await waitFor(() => expect(screen.getByText('Practice')).toBeInTheDocument());

    (globalThis as any).fetch = originalFetch;
    vi.restoreAllMocks();
  });
});
