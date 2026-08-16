import { apiRequest, toQueryString } from './client';
import type {
  CreateSessionRequest,
  Session,
  SessionListParams,
  UpdateSessionRequest,
} from './contracts';

export function getSessions(params: SessionListParams = {}): Promise<Session[]> {
  return apiRequest<Session[]>(`/sessions${toQueryString({
    include_deleted: params.include_deleted,
  })}`);
}

export function getSession(id: string): Promise<Session> {
  return apiRequest<Session>(`/sessions/${id}`);
}

export function createSession(payload: CreateSessionRequest): Promise<Session> {
  return apiRequest<Session>('/sessions', { method: 'POST', body: payload });
}

export function updateSession(id: string, payload: UpdateSessionRequest): Promise<Session> {
  return apiRequest<Session>(`/sessions/${id}`, { method: 'PATCH', body: payload });
}

export function deleteSession(id: string): Promise<void> {
  return apiRequest<void>(`/sessions/${id}`, { method: 'DELETE' });
}

export function restoreSession(id: string): Promise<Session> {
  return apiRequest<Session>(`/sessions/${id}/restore`, { method: 'POST' });
}
