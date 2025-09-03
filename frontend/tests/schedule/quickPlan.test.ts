import { initQuickPlan } from '../../components/quickPlan.js';
import defaultPlan from './fixtures/defaultPlan.json';
import { vi } from 'vitest';

describe('quick plan', () => {
  test('renders and saves template', async () => {
    document.body.innerHTML = '<div id="quickPlan"></div>';
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(defaultPlan), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      )
      .mockResolvedValue(
        new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } })
      );
    const originalFetch = global.fetch;
    vi.stubGlobal('fetch', fetchMock);

    initQuickPlan();
    await new Promise((r) => setTimeout(r, 0));

    const practice = document.querySelector('input[name="practice"]') as HTMLInputElement;
    expect(practice.checked).toBe(true);

    const rest = document.querySelector('input[name="rest"]') as HTMLInputElement;
    rest.checked = true;
    document.querySelector('#quickPlan form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true })
    );
    await new Promise((r) => setTimeout(r, 0));

    expect(fetchMock.mock.calls[1][0]).toBe('/api/default-plan');
    const body = fetchMock.mock.calls[1][1]?.body as string;
    expect(JSON.parse(body)).toEqual({ practice: true, rest: true, travel: true });

    (global as any).fetch = originalFetch;
  });
});
