import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ModerationQueue } from '../src/admin/moderation';

test('lists submissions and posts review', async () => {
  const fetchMock = vi
    .fn()
    // initial load
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify([{ id: 1, name: 'Skin', status: 'pending' }]),
        { headers: { 'Content-Type': 'application/json' } }
      )
    )
    // review call
    .mockResolvedValueOnce(new Response('{}', { headers: { 'Content-Type': 'application/json' } }))
    // reload after review
    .mockResolvedValueOnce(new Response('[]', { headers: { 'Content-Type': 'application/json' } }));

  // override global fetch for this test
  (global as any).fetch = fetchMock;

  render(<ModerationQueue />);
  expect(await screen.findByText('Skin')).toBeInTheDocument();

  fireEvent.click(screen.getByText('Approve'));

  await waitFor(() => {
    expect(fetchMock).toHaveBeenCalledWith('/admin/media/review/1/approve', { method: 'POST' });
  });
});

