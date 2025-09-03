import { renderSchedule } from '../components/scheduleRenderer.js';
import { initSchedulePage } from '../components/schedule.js';
import { vi } from 'vitest';

describe('schedule components', () => {
  test('renders hourly entries', () => {
    const container = document.createElement('div');
    renderSchedule(container, { mode: 'hourly', entries: { '08:00': 'Practice' } });
    expect(container.textContent).toContain('08:00');
  });

  test('submits hourly schedule', async () => {
    document.body.innerHTML = `
      <form id="scheduleForm">
        <label><input type="radio" name="mode" value="hourly" checked></label>
        <label><input type="radio" name="mode" value="category"></label>
        <div id="hourlyFields"></div>
        <div id="categoryField" style="display:none;">
          <select id="categorySelect" name="category">
            <option value="practice">Practice</option>
          </select>
        </div>
        <button type="submit">Save</button>
      </form>
      <div id="scheduleDisplay"></div>
    `;
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ mode: 'hourly', entries: { '01:00': 'Jam' } }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    const originalFetch = global.fetch;
    vi.stubGlobal('fetch', fetchMock);

    initSchedulePage();

    const input = document.querySelector('[name="h1"]') as HTMLInputElement;
    input.value = 'Jam';
    document.getElementById('scheduleForm')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    await new Promise((r) => setTimeout(r, 0));

    expect(fetchMock).toHaveBeenCalledWith('/api/schedule', expect.objectContaining({ method: 'POST' }));
    expect(document.getElementById('scheduleDisplay')!.textContent).toContain('01:00');

    (global as any).fetch = originalFetch;
  });
});
