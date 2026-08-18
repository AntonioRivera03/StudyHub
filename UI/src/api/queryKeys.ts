export const queryKeys = {
  dashboard: (timezoneOffsetMinutes: number) => ['dashboard', timezoneOffsetMinutes] as const,
  activeTimer: ['timer', 'active'] as const,
  studyFlow: (sessionId: string | null) => (
    ['timer', 'study-flow', sessionId ?? 'active'] as const
  ),
  settings: ['settings', 'pomodoro'] as const,
  categories: ['categories'] as const,
  sessions: (includeDeleted = false) => ['sessions', { includeDeleted }] as const,
  decks: (includeDeleted = false) => ['decks', { includeDeleted }] as const,
  deck: (deckId: string, includeDeleted = false) => (
    ['decks', deckId, { includeDeleted }] as const
  ),
  cards: (deckId: string, includeDeleted = false) => (
    ['decks', deckId, 'cards', { includeDeleted }] as const
  ),
  card: (cardId: string, includeDeleted = false) => (
    ['cards', cardId, { includeDeleted }] as const
  ),
  dueCards: (deckId: string) => ['decks', deckId, 'due-cards'] as const,
  reviews: (includeDeleted = false) => ['reviews', { includeDeleted }] as const,
  activeReview: ['reviews', 'active'] as const,
  review: (reviewId: string) => ['reviews', reviewId] as const,
  reviewNext: (reviewId: string) => ['reviews', reviewId, 'next'] as const,
};
