import React from 'react';
import { render, screen } from '@testing-library/react';
import { WebsocketMetricsWidget } from '../src/admin/dashboard';

test('renders metrics from websocket messages', async () => {
  let socket: any;
  class MockWS {
    onopen: ((ev: any) => any) | null = null;
    onmessage: ((ev: any) => any) | null = null;
    constructor(url: string) {
      socket = this;
    }
    send() {}
    close() {}
  }
  (global as any).WebSocket = MockWS as any;

  render(<WebsocketMetricsWidget />);
  socket.onopen && socket.onopen({});
  socket.onmessage &&
    socket.onmessage({
      data: JSON.stringify({ topic: 'metrics', data: { connections: 2, messages: 5 } }),
    });
  expect(await screen.findByText(/Connections: 2/)).toBeInTheDocument();
  expect(await screen.findByText(/Messages: 5/)).toBeInTheDocument();
});
