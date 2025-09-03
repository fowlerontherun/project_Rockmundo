import { initAdvancedPlanner, updateSlot } from '../../components/advancedPlanner.js';
import sched from './fixtures/schedule.json';
import { vi } from 'vitest';

describe('advanced planner', () => {
  test('renders grid and handles granular edits', async () => {
    document.body.innerHTML = '<div id="advancedPlanner"></div>';
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

    initAdvancedPlanner();
    await new Promise((r) => setTimeout(r, 0));

    const slots = document.querySelectorAll('#plannerGrid .slot');
    expect(slots.length).toBe(96);
    const slot0000 = document.querySelector('[data-time="00:00"]');
    expect(slot0000!.textContent).toContain('Sleep');

    await updateSlot('00:15', 'Practice');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/schedule/00:15',
      expect.objectContaining({ method: 'PUT' })
    );
    const slot0015 = document.querySelector('[data-time="00:15"]');
    expect(slot0015!.textContent).toContain('Practice');

    (global as any).fetch = originalFetch;
  });
});
