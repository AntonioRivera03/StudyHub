import type { ActiveTimer, Category, PomodoroSettings, Session } from '../api/contracts';

export const categoryFixture: Category = {
  id: 'category-1',
  name: 'Coursework',
  color: '#798186',
  created_at: '2026-08-16T08:00:00.000Z',
  updated_at: '2026-08-16T08:00:00.000Z',
  deleted_at: null,
};

export const settingsFixture: PomodoroSettings = {
  focus_minutes: 25,
  short_break_minutes: 5,
  long_break_minutes: 15,
  long_break_every: 4,
  created_at: '2026-08-16T08:00:00.000Z',
  updated_at: '2026-08-16T08:00:00.000Z',
};

export const sessionFixture: Session = {
  id: 'session-1',
  title: 'Read notes',
  category_id: categoryFixture.id,
  source: 'pomodoro',
  status: 'completed',
  started_at: '2026-08-16T09:00:00.000Z',
  ended_at: '2026-08-16T09:40:00.000Z',
  duration_seconds: 1500,
  notes: null,
  timer_id: 'timer-1',
  created_at: '2026-08-16T09:25:00.000Z',
  updated_at: '2026-08-16T09:25:00.000Z',
  deleted_at: null,
};

export function activeTimerFixture(overrides: Partial<ActiveTimer> = {}): ActiveTimer {
  return {
    id: 'timer-1',
    phase: 'focus',
    state: 'running',
    title: 'Practice recall',
    category_id: categoryFixture.id,
    duration_seconds: 1500,
    started_at: new Date(Date.now() - 60_000).toISOString(),
    expected_end_at: new Date(Date.now() + 5 * 60_000).toISOString(),
    remaining_seconds: 300,
    paused_at: null,
    completed_at: null,
    cancelled_at: null,
    created_at: new Date(Date.now() - 60_000).toISOString(),
    updated_at: new Date(Date.now() - 60_000).toISOString(),
    ...overrides,
  };
}
