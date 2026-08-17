import { apiRequest } from './client';
import type { ActiveStudyFlow, ActiveTimer, StartTimerRequest } from './contracts';

export function getActiveTimer(): Promise<ActiveTimer | null> {
  return apiRequest<ActiveTimer | null>('/timer/active');
}

export function getActiveStudyFlow(): Promise<ActiveStudyFlow | null> {
  return apiRequest<ActiveStudyFlow | null>('/timer/study-flow/active');
}

export function getStudyFlow(sessionId: string): Promise<ActiveStudyFlow> {
  return apiRequest<ActiveStudyFlow>(`/timer/study-flow/${sessionId}`);
}

export function confirmStudyFlowSegment(
  sessionId: string,
  segmentIndex: number,
): Promise<ActiveStudyFlow> {
  return apiRequest<ActiveStudyFlow>(
    `/timer/study-flow/${sessionId}/segments/${segmentIndex}/confirm`,
    { method: 'POST' },
  );
}

export function startTimer(payload: StartTimerRequest): Promise<ActiveTimer> {
  return apiRequest<ActiveTimer>('/timer/start', { method: 'POST', body: payload });
}

export function pauseTimer(id: string): Promise<ActiveTimer> {
  return apiRequest<ActiveTimer>(`/timer/${id}/pause`, { method: 'POST' });
}

export function resumeTimer(id: string): Promise<ActiveTimer> {
  return apiRequest<ActiveTimer>(`/timer/${id}/resume`, { method: 'POST' });
}

export function completeTimer(id: string): Promise<ActiveTimer> {
  return apiRequest<ActiveTimer>(`/timer/${id}/complete`, { method: 'POST' });
}

export function cancelTimer(id: string): Promise<ActiveTimer> {
  return apiRequest<ActiveTimer>(`/timer/${id}/cancel`, { method: 'POST' });
}
