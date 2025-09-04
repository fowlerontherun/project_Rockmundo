import { initMobilePlanner } from '../../components/mobilePlanner.js';
import sched from './fixtures/schedule.json';
import { vi } from 'vitest';

describe('mobile planner', () => {
  test('renders and saves via touch controls', async () => {
    document.body.innerHTML = '<div id="mobilePlanner"></div>';
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ mode: 'hourly', entries: sched }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ mode: 'hourly', entries: { '01:00': 'Jam' } }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      );
    const originalFetch = global.fetch;
    vi.stubGlobal('fetch', fetchMock);

    initMobilePlanner();
    await new Promise((r) => setTimeout(r, 0));

    expect(document.getElementById('mobileDisplay').textContent).toContain('Sleep');

    const time = document.querySelector('input[name="time"]');
    const value = document.querySelector('input[name="value"]');
    time.value = '01:00';
    value.value = 'Jam';
    document.querySelector('#mobilePlanner form').dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true })
    );
    await new Promise((r) => setTimeout(r, 0));

    expect(fetchMock.mock.calls[1][0]).toBe('/api/schedule');
    expect(document.getElementById('mobileDisplay').textContent).toContain('Jam');

    global.fetch = originalFetch;
  });
});
