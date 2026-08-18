import type { components } from './generated';

type Schemas = components['schemas'];

export type TimerPhase = Schemas['TimerPhase'];
export type TimerState = Schemas['TimerState'];
export type SessionSource = Schemas['SessionSource'];
export type SessionStatus = Schemas['SessionStatus'];

export type HealthResponse = Schemas['HealthResponse'];

export type Category = Schemas['CategoryResponse'];
export type CreateCategoryRequest = Schemas['CategoryCreate'];
export type UpdateCategoryRequest = Schemas['CategoryUpdate'];

export type PomodoroSettings = Schemas['PomodoroSettingsResponse'];
export type UpdatePomodoroSettingsRequest = Schemas['PomodoroSettingsUpdate'];

export type ActiveTimer = Schemas['TimerResponse'];
export type StartTimerRequest = Schemas['TimerStart'];
export type ActiveStudyFlow = Schemas['StudyFlowStateResponse'];

export type Session = Schemas['StudySessionResponse'];
export type CreateSessionRequest = Schemas['StudySessionCreate'];
export type UpdateSessionRequest = Schemas['StudySessionUpdate'];

export interface SessionListParams {
  include_deleted?: boolean;
}

export type DashboardSummary = Schemas['DashboardSummaryResponse'];

export type ReviewRating = Schemas['ReviewRating'];
export type FlashcardDeck = Schemas['FlashcardDeckResponse'];
export type Flashcard = Schemas['FlashcardResponse'];
export type ReviewSession = Schemas['ReviewSessionResponse'];
export type ReviewProgress = Schemas['ReviewProgressResponse'];
export type ReviewEvent = Schemas['ReviewEventResponse'];
export type ReviewRatingResult = Schemas['ReviewRatingResultResponse'];
export type CreateDeckRequest = Schemas['FlashcardDeckCreate'];
export type UpdateDeckRequest = Schemas['FlashcardDeckUpdate'];
export type CreateCardRequest = Schemas['FlashcardCreate'];
export type UpdateCardRequest = Schemas['FlashcardUpdate'];
export type StartReviewRequest = Schemas['ReviewStart'];
export type RateCardRequest = Schemas['ReviewRatingCreate'];
