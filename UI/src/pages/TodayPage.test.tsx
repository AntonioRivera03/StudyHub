import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderWithProviders } from '../test/render';
import { categoryFixture, sessionFixture } from '../test/fixtures';
import { TodayPage } from './TodayPage';

const mocks = vi.hoisted(() => ({
  getDashboardSummary: vi.fn(),
  getCategories: vi.fn(),
  getSessions: vi.fn(),
  deleteSession: vi.fn(),
  restoreSession: vi.fn(),
}));

vi.mock('../api/dashboard', () => ({ getDashboardSummary: mocks.getDashboardSummary }));
vi.mock('../api/categories', () => ({ getCategories: mocks.getCategories }));
vi.mock('../api/sessions', () => ({
  getSessions: mocks.getSessions,
  deleteSession: mocks.deleteSession,
  restoreSession: mocks.restoreSession,
}));

describe('TodayPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getCategories.mockResolvedValue([categoryFixture]);
    mocks.deleteSession.mockResolvedValue(undefined);
    mocks.restoreSession.mockResolvedValue(sessionFixture);
  });

  it('directs an empty day to the focus loop', async () => {
    mocks.getDashboardSummary.mockResolvedValue({
      today_completed_focus_minutes: 0,
      today_completed_session_count: 0,
      active_timer: null,
      recent_sessions: [],
    });
    mocks.getSessions.mockResolvedValue([]);

    renderWithProviders(<TodayPage />);

    expect(await screen.findByRole('heading', { name: 'Make one interval count.' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Start focusing' })).toHaveAttribute('href', '/focus');
    expect(await screen.findByText('No sessions recorded yet')).toBeInTheDocument();
  });

  it('shows populated summary values and recent rows', async () => {
    mocks.getDashboardSummary.mockResolvedValue({
      today_completed_focus_minutes: 65,
      today_completed_session_count: 2,
      active_timer: null,
      recent_sessions: [sessionFixture],
    });
    mocks.getSessions.mockResolvedValue([sessionFixture]);

    renderWithProviders(<TodayPage />);

    expect(await screen.findByText('1h 5m')).toBeInTheDocument();
    expect(await screen.findByText('Read notes')).toBeInTheDocument();
    expect(screen.getByText('Coursework')).toBeInTheDocument();
    expect(screen.getByText('25m')).toBeInTheDocument();
    expect(screen.queryByText('40m')).not.toBeInTheDocument();
    expect(screen.queryByText('Make one interval count.')).not.toBeInTheDocument();
  });
});
