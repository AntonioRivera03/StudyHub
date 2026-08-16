import { describe, expect, it } from 'vitest';
import { deriveRemainingSeconds, formatDuration, formatTimer, getGreeting } from './time';

describe('timer formatting', () => {
  it('derives remaining time from the expected server end time', () => {
    const now = Date.parse('2026-08-16T10:00:00.000Z');
    expect(deriveRemainingSeconds('2026-08-16T10:01:00.000Z', now)).toBe(60);
    expect(deriveRemainingSeconds('2026-08-16T10:00:00.001Z', now)).toBe(1);
    expect(deriveRemainingSeconds('2026-08-16T09:59:00.000Z', now)).toBe(0);
    expect(deriveRemainingSeconds('not-a-date', now)).toBe(0);
  });

  it('formats timer and summary durations', () => {
    expect(formatTimer(1500)).toBe('25:00');
    expect(formatTimer(3661)).toBe('01:01:01');
    expect(formatDuration(3900)).toBe('1h 5m');
    expect(formatDuration(30)).toBe('<1m');
    expect(formatDuration(0)).toBe('0m');
  });

  it('selects a greeting from the local hour', () => {
    expect(getGreeting(8)).toBe('Good morning');
    expect(getGreeting(15)).toBe('Good afternoon');
    expect(getGreeting(21)).toBe('Good evening');
  });
});
