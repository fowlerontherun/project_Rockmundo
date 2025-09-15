// Simple helper for WebSocket connections with polling fallback.
//
// Usage:
//   import { connect } from './utils/ws.js';
//   const conn = connect('/notifications/ws', {
//     onMessage: (msg) => console.log(msg),
//     pollUrl: '/api/notifications', // fallback endpoint returning JSON list
//   });
//
// The returned object exposes `send` and `close` regardless of whether a
// WebSocket or polling is used.

import { authFetch } from './auth.js';

export function connect(url, { onMessage, onError, onOpen, pollUrl, pollInterval = 5000 } = {}) {
  if (!/^wss?:/i.test(url)) {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    url = `${proto}://${window.location.host}${url}`;
  }
  // If WebSocket is supported and available, prefer it.
  if ('WebSocket' in window) {
    try {
      const ws = new WebSocket(url);
      ws.onmessage = (ev) => onMessage && onMessage(ev.data);
      ws.onerror = (err) => onError && onError(err);
      ws.onopen = () => onOpen && onOpen(ws);
      ws.onclose = () => {
        onError && onError(new Error('ws_closed'));
        if (pollUrl) startPolling();
      };
      return {
        send: (data) => ws.readyState === WebSocket.OPEN && ws.send(data),
        close: () => ws.close(),
      };
    } catch (err) {
      onError && onError(err);
      if (!pollUrl) throw err;
      return startPolling();
    }
  }
  // Fallback to polling when WS unsupported or fails
  return startPolling();

  function startPolling() {
    let timer;
    const controller = {
      send() {},
      close() {
        if (timer) clearInterval(timer);
      },
    };
    async function poll() {
      try {
        const res = await authFetch(pollUrl);
        if (res.ok) {
          const data = await res.json();
          onMessage && onMessage(data);
        }
      } catch (err) {
        onError && onError(err);
      }
    }
    timer = setInterval(poll, pollInterval);
    poll();
    onOpen && onOpen(controller);
    return controller;
  }
}
