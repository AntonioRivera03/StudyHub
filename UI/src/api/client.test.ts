import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { getHealth } from './health';
import { startTimer } from './timer';
import { server } from '../test/server';

describe('API client', () => {
  it('uses the versioned API prefix and parses typed JSON', async () => {
    server.use(
      http.get('*/api/v1/health', () => HttpResponse.json({ status: 'ok' })),
    );

    await expect(getHealth()).resolves.toEqual({ status: 'ok' });
  });

  it('surfaces the server error message', async () => {
    server.use(
      http.post('*/api/v1/timer/start', () => HttpResponse.json(
        { error: { code: 'conflict', message: 'A timer is already active' } },
        { status: 409 },
      )),
    );

    await expect(startTimer({ phase: 'focus' })).rejects.toThrow('A timer is already active');
  });
});
