export const queryKeys = {
  dashboard: (timezoneOffsetMinutes: number) => ['dashboard', timezoneOffsetMinutes] as const,
  activeTimer: ['timer', 'active'] as const,
  studyFlow: (sessionId: string | null) => (
    ['timer', 'study-flow', sessionId ?? 'active'] as const
  ),
  settings: ['settings', 'pomodoro'] as const,
  categories: ['categories'] as const,
  sessions: (includeDeleted = false) => ['sessions', { includeDeleted }] as const,
};
