export function deriveRemainingSeconds(expectedEndAt: string, nowMs = Date.now()): number {
  const endMs = Date.parse(expectedEndAt);
  if (Number.isNaN(endMs)) return 0;
  return Math.max(0, Math.ceil((endMs - nowMs) / 1000));
}

export function formatTimer(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;
  if (hours > 0) {
    return [hours, minutes, seconds].map((part) => String(part).padStart(2, '0')).join(':');
  }
  return [minutes, seconds].map((part) => String(part).padStart(2, '0')).join(':');
}

export function formatDuration(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  if (safeSeconds === 0) return '0m';
  if (safeSeconds < 60) return '<1m';
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  if (hours === 0) return `${minutes}m`;
  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
}

export function formatSessionTime(startedAt: string, endedAt: string | null): string {
  const formatter = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
  return endedAt
    ? `${formatter.format(new Date(startedAt))} - ${formatter.format(new Date(endedAt))}`
    : `${formatter.format(new Date(startedAt))} - ongoing`;
}

export function getSessionDurationSeconds(startedAt: string, endedAt: string | null, nowMs = Date.now()): number {
  const startMs = Date.parse(startedAt);
  const endMs = endedAt ? Date.parse(endedAt) : nowMs;
  if (Number.isNaN(startMs) || Number.isNaN(endMs)) return 0;
  return Math.max(0, Math.floor((endMs - startMs) / 1000));
}

export function toLocalDateTimeInput(date: Date): string {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

export function getGreeting(hour: number): string {
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}
