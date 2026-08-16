import { apiRequest } from './client';
import type { HealthResponse } from './contracts';

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health');
}
