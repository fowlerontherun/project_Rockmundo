export function createFetchMock() {
  return async (input: RequestInfo, init?: RequestInit): Promise<Response> => {
    const url = typeof input === 'string' ? input : input.toString();
    if (url.endsWith('/admin/monitoring/metrics')) {
      return new Response(
        JSON.stringify({ cpu: 10, memory: 20, active_sessions: 5 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }
    return new Response('{}', {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  };
}
