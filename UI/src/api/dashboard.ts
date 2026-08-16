import { apiRequest, toQueryString } from './client';
import type { DashboardSummary } from './contracts';

export function getDashboardSummary(timezoneOffsetMinutes: number): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>(
    `/dashboard/summary${toQueryString({ timezone_offset_minutes: timezoneOffsetMinutes })}`,
  );
}
