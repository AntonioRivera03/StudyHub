import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { activeTimerFixture, categoryFixture, settingsFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { FocusPage } from './FocusPage';

const mocks = vi.hoisted(() => ({
  getCategories: vi.fn(),
  getPomodoroSettings: vi.fn(),
  updatePomodoroSettings: vi.fn(),
  getActiveTimer: vi.fn(),
  startTimer: vi.fn(),
  pauseTimer: vi.fn(),
  resumeTimer: vi.fn(),
  completeTimer: vi.fn(),
  cancelTimer: vi.fn(),
}));

vi.mock('../api/categories', () => ({ getCategories: mocks.getCategories }));
vi.mock('../api/settings', () => ({
  getPomodoroSettings: mocks.getPomodoroSettings,
  updatePomodoroSettings: mocks.updatePomodoroSettings,
}));
vi.mock('../api/timer', () => ({
  getActiveTimer: mocks.getActiveTimer,
  startTimer: mocks.startTimer,
  pauseTimer: mocks.pauseTimer,
  resumeTimer: mocks.resumeTimer,
  completeTimer: mocks.completeTimer,
  cancelTimer: mocks.cancelTimer,
}));

describe('FocusPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getCategories.mockResolvedValue([categoryFixture]);
    mocks.getPomodoroSettings.mockResolvedValue(settingsFixture);
    mocks.updatePomodoroSettings.mockResolvedValue(settingsFixture);
    mocks.resumeTimer.mockResolvedValue(activeTimerFixture());
    mocks.completeTimer.mockResolvedValue(activeTimerFixture({ state: 'completed' }));
    mocks.cancelTimer.mockResolvedValue(activeTimerFixture({ state: 'cancelled' }));
  });

  it('shows idle setup and starts a categorized focus timer', async () => {
    const user = userEvent.setup();
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.startTimer.mockResolvedValue(activeTimerFixture());

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByText('25:00')).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Category'), categoryFixture.id);
    await user.type(screen.getByLabelText(/Focus title/), 'Practice recall');
    await user.click(screen.getByRole('button', { name: 'Start focus' }));

    await waitFor(() => {
      expect(mocks.startTimer).toHaveBeenCalledWith({
        phase: 'focus',
        category_id: categoryFixture.id,
        title: 'Practice recall',
      });
    });
  });

  it('starts an uncategorized focus timer when no categories exist', async () => {
    const user = userEvent.setup();
    mocks.getCategories.mockResolvedValue([]);
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.startTimer.mockResolvedValue(activeTimerFixture({ category_id: null, title: null }));

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByRole('option', { name: 'Unsorted / No category' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create your first category' })).toBeInTheDocument();
    const startButton = screen.getByRole('button', { name: 'Start focus' });
    expect(startButton).toBeEnabled();
    await user.click(startButton);

    await waitFor(() => {
      expect(mocks.startTimer).toHaveBeenCalledWith({
        phase: 'focus',
        category_id: null,
        title: null,
      });
    });
  });

  it('recovers an active timer and exposes running controls', async () => {
    const user = userEvent.setup();
    const activeTimer = activeTimerFixture();
    mocks.getActiveTimer.mockResolvedValue(activeTimer);
    mocks.pauseTimer.mockResolvedValue({ ...activeTimer, state: 'paused', remaining_seconds: 299 });

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByRole('button', { name: 'Pause' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finish session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Start focus' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Pause' }));
    await waitFor(() => expect(mocks.pauseTimer).toHaveBeenCalledWith(activeTimer.id));
  });
});
