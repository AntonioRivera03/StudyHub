import { apiRequest } from './client';
import type { PomodoroSettings, UpdatePomodoroSettingsRequest } from './contracts';

export function getPomodoroSettings(): Promise<PomodoroSettings> {
  return apiRequest<PomodoroSettings>('/settings/pomodoro');
}

export function updatePomodoroSettings(payload: UpdatePomodoroSettingsRequest): Promise<PomodoroSettings> {
  return apiRequest<PomodoroSettings>('/settings/pomodoro', { method: 'PATCH', body: payload });
}
