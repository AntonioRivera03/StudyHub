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

export type Session = Schemas['StudySessionResponse'];
export type CreateSessionRequest = Schemas['StudySessionCreate'];
export type UpdateSessionRequest = Schemas['StudySessionUpdate'];

export interface SessionListParams {
  include_deleted?: boolean;
}

export type DashboardSummary = Schemas['DashboardSummaryResponse'];
