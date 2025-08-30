import { beforeAll, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { createFetchMock } from './mockApi';

beforeAll(() => {
  vi.stubGlobal('fetch', createFetchMock());
  class MockWebSocket {
    url: string;
    onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
    send() {}
    close() {}
    constructor(url: string) {
      this.url = url;
    }
  }
  vi.stubGlobal('WebSocket', MockWebSocket as any);
});

afterEach(() => {
  cleanup();
});
