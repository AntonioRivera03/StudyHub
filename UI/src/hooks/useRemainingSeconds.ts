import { useEffect, useState } from 'react';
import { deriveRemainingSeconds } from '../lib/time';

export function useRemainingSeconds(expectedEndAt: string | null, running: boolean): number {
  const [nowMs, setNowMs] = useState(Date.now);

  useEffect(() => {
    if (!running || !expectedEndAt) return undefined;
    setNowMs(Date.now());
    const interval = window.setInterval(() => setNowMs(Date.now()), 500);
    return () => window.clearInterval(interval);
  }, [expectedEndAt, running]);

  return expectedEndAt ? deriveRemainingSeconds(expectedEndAt, nowMs) : 0;
}
