import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ItemDetail from '../src/items/ItemDetail';

test('renders durability bar and triggers repair', async () => {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ new_durability: 100 }),
  });
  const originalFetch = global.fetch;
  vi.stubGlobal('fetch', fetchMock);

  render(<ItemDetail id={1} name="Sword" durability={50} ownerId={2} />);
  const bar = screen.getByRole('progressbar');
  expect(bar).toHaveStyle('width: 50%');
  const btn = screen.getByText(/repair/i);
  btn.click();
  expect(fetchMock).toHaveBeenCalledWith(
    '/shop/items/1/repair',
    expect.objectContaining({ method: 'POST' })
  );
  (global as any).fetch = originalFetch;
});
