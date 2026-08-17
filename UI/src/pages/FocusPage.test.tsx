import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { activeTimerFixture, categoryFixture, settingsFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { FocusPage } from './FocusPage';

const mocks = vi.hoisted(() => ({
  getCategories: vi.fn(),
  getPomodoroSettings: vi.fn(),
  updatePomodoroSettings: vi.fn(),
  getActiveTimer: vi.fn(),
  getActiveStudyFlow: vi.fn(),
  getStudyFlow: vi.fn(),
  startTimer: vi.fn(),
  pauseTimer: vi.fn(),
  resumeTimer: vi.fn(),
  completeTimer: vi.fn(),
  cancelTimer: vi.fn(),
  confirmStudyFlowSegment: vi.fn(),
}));

const localStorageValues = new Map<string, string>();
Object.defineProperty(window, 'localStorage', {
  configurable: true,
  value: {
    get length() {
      return localStorageValues.size;
    },
    clear: () => localStorageValues.clear(),
    getItem: (key: string) => localStorageValues.get(key) ?? null,
    key: (index: number) => Array.from(localStorageValues.keys())[index] ?? null,
    removeItem: (key: string) => localStorageValues.delete(key),
    setItem: (key: string, value: string) => localStorageValues.set(key, value),
  } satisfies Storage,
});

vi.mock('../api/categories', () => ({ getCategories: mocks.getCategories }));
vi.mock('../api/settings', () => ({
  getPomodoroSettings: mocks.getPomodoroSettings,
  updatePomodoroSettings: mocks.updatePomodoroSettings,
}));
vi.mock('../api/timer', () => ({
  getActiveTimer: mocks.getActiveTimer,
  getActiveStudyFlow: mocks.getActiveStudyFlow,
  getStudyFlow: mocks.getStudyFlow,
  startTimer: mocks.startTimer,
  pauseTimer: mocks.pauseTimer,
  resumeTimer: mocks.resumeTimer,
  completeTimer: mocks.completeTimer,
  cancelTimer: mocks.cancelTimer,
  confirmStudyFlowSegment: mocks.confirmStudyFlowSegment,
}));

describe('FocusPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    mocks.getCategories.mockResolvedValue([categoryFixture]);
    mocks.getPomodoroSettings.mockResolvedValue(settingsFixture);
    mocks.getActiveStudyFlow.mockResolvedValue(null);
    mocks.getStudyFlow.mockRejectedValue(new ApiError('StudyFlow session not found', 404));
    mocks.updatePomodoroSettings.mockResolvedValue(settingsFixture);
    mocks.resumeTimer.mockResolvedValue(activeTimerFixture());
    mocks.completeTimer.mockResolvedValue(activeTimerFixture({ state: 'completed' }));
    mocks.cancelTimer.mockResolvedValue(activeTimerFixture({ state: 'cancelled' }));
    mocks.confirmStudyFlowSegment.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: 'active',
      current_segment_index: 1,
      awaiting_confirmation: false,
      active_timer: null,
    });
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

  it('opens StudyFlow with the fixed six-segment sequence', async () => {
    const user = userEvent.setup();
    mocks.getActiveTimer.mockResolvedValue(null);

    const { container } = renderWithProviders(<FocusPage />, '/focus');

    await user.click(await screen.findByRole('button', { name: 'StudyFlow' }));

    const segmentLabels = [
      'Focus #1',
      'S-Break #1',
      'Focus #2',
      'S-Break #2',
      'Focus #3',
      'L-Break #1',
    ];
    expect(screen.getByRole('region', { name: 'A longer rhythm, mapped out.' })).toBeInTheDocument();
    segmentLabels.forEach((label) => expect(screen.getByText(label)).toBeInTheDocument());
    expect(screen.getByText('Focus #1').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('25 min / not started')).toBeInTheDocument();
    expect(container.querySelectorAll('[data-study-flow-indicator]')).toHaveLength(1);
    expect(container.querySelector('[data-study-flow-indicator="not-started"]')).toBeInTheDocument();
    expect(screen.queryByLabelText('Timer phase')).not.toBeInTheDocument();
  });

  it('only advances StudyFlow after finishing the current segment', async () => {
    const user = userEvent.setup();
    const activeTimer = activeTimerFixture({
      study_flow_session_id: 'study-flow-1',
      study_flow_segment_index: 0,
    });
    let serverTimer: ReturnType<typeof activeTimerFixture> | null = null;
    let serverSegmentIndex = 0;
    mocks.getActiveTimer.mockImplementation(() => Promise.resolve(serverTimer));
    mocks.getStudyFlow.mockImplementation(() => Promise.resolve({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: 'active',
      current_segment_index: serverSegmentIndex,
      awaiting_confirmation: false,
      active_timer: serverTimer,
    }));
    mocks.startTimer.mockImplementation(() => {
      serverTimer = activeTimer;
      return Promise.resolve(activeTimer);
    });
    mocks.completeTimer.mockImplementation(() => {
      serverTimer = null;
      serverSegmentIndex = 1;
      return Promise.resolve(activeTimerFixture({ state: 'completed' }));
    });

    renderWithProviders(<FocusPage />, '/focus');

    await user.click(await screen.findByRole('button', { name: 'StudyFlow' }));
    await user.click(screen.getByRole('button', { name: 'Start focus' }));
    await waitFor(() => expect(mocks.startTimer).toHaveBeenCalledWith({
      phase: 'focus',
      category_id: null,
      title: null,
      study_flow_session_id: null,
      study_flow_segment_index: 0,
    }));
    expect(await screen.findByRole('button', { name: 'Pause' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Finish Segment' })).toBeInTheDocument();
    expect(screen.getByText('Focus #1').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Focus #1').closest('li')?.querySelector('[data-study-flow-indicator="in-progress"]')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Finish Segment' }));

    await waitFor(() => expect(mocks.completeTimer).toHaveBeenCalledWith(activeTimer.id));
    expect(await screen.findByRole('button', { name: 'Start short break' })).toBeInTheDocument();
    expect(screen.getByText('S-Break #1').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Focus #1').closest('li')).not.toHaveAttribute('aria-current');
    expect(screen.getByText('Focus #1').closest('li')?.querySelector('[data-study-flow-indicator="past"]')).toBeInTheDocument();
    expect(screen.getByText('S-Break #1').closest('li')?.querySelector('[data-study-flow-indicator="not-started"]')).toBeInTheDocument();

    mocks.startTimer.mockClear();
    await user.click(screen.getByRole('button', { name: 'Start short break' }));
    await waitFor(() => expect(mocks.startTimer).toHaveBeenCalledWith({
      phase: 'short_break',
      category_id: null,
      title: null,
      study_flow_session_id: 'study-flow-1',
      study_flow_segment_index: 1,
    }));
  });

  it('resets StudyFlow when the current pipeline is canceled', async () => {
    const user = userEvent.setup();
    const activeTimer = activeTimerFixture({
      study_flow_session_id: 'study-flow-1',
      study_flow_segment_index: 0,
    });
    let serverTimer: ReturnType<typeof activeTimerFixture> | null = null;
    let flowWasCanceled = false;
    mocks.getActiveTimer.mockImplementation(() => Promise.resolve(serverTimer));
    mocks.getStudyFlow.mockImplementation(() => Promise.resolve({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: flowWasCanceled ? 'cancelled' : 'active',
      current_segment_index: 0,
      awaiting_confirmation: false,
      active_timer: serverTimer,
    }));
    mocks.startTimer.mockImplementation(() => {
      serverTimer = activeTimer;
      return Promise.resolve(activeTimer);
    });
    mocks.cancelTimer.mockImplementation(() => {
      serverTimer = null;
      flowWasCanceled = true;
      return Promise.resolve(activeTimerFixture({
        state: 'cancelled',
        study_flow_session_id: 'study-flow-1',
        study_flow_segment_index: 0,
      }));
    });

    renderWithProviders(<FocusPage />, '/focus');

    await user.click(await screen.findByRole('button', { name: 'StudyFlow' }));
    await user.click(screen.getByRole('button', { name: 'Start focus' }));
    expect(await screen.findByRole('button', { name: 'Pause' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    await waitFor(() => expect(mocks.cancelTimer).toHaveBeenCalledWith(activeTimer.id));
    expect(await screen.findByRole('button', { name: 'Start focus' })).toBeInTheDocument();
    expect(screen.getByText('Focus #1').closest('li')).toHaveAttribute('aria-current', 'step');

    mocks.startTimer.mockClear();
    await user.click(screen.getByRole('button', { name: 'Start focus' }));
    await waitFor(() => expect(mocks.startTimer).toHaveBeenCalledWith(expect.objectContaining({
      study_flow_session_id: null,
      study_flow_segment_index: 0,
    })));
  });

  it('requires Finish Segment after a StudyFlow timer expires', async () => {
    const user = userEvent.setup();
    const activeTimer = activeTimerFixture({
      study_flow_session_id: 'study-flow-1',
      study_flow_segment_index: 0,
    });
    let serverTimer: ReturnType<typeof activeTimerFixture> | null = null;
    let segmentWasConfirmed = false;
    mocks.getActiveTimer.mockImplementation(() => Promise.resolve(serverTimer));
    mocks.getStudyFlow.mockImplementation(() => Promise.resolve({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: 'active',
      current_segment_index: segmentWasConfirmed ? 1 : 0,
      awaiting_confirmation: serverTimer === null && !segmentWasConfirmed,
      active_timer: serverTimer,
    }));
    mocks.confirmStudyFlowSegment.mockImplementation(() => {
      segmentWasConfirmed = true;
      return Promise.resolve({
        session_id: 'study-flow-1',
        title: 'StudyFlow session',
        category_id: null,
        status: 'active',
        current_segment_index: 1,
        awaiting_confirmation: false,
        active_timer: null,
      });
    });
    mocks.startTimer.mockImplementation(() => {
      serverTimer = activeTimer;
      return Promise.resolve(activeTimer);
    });

    const { queryClient } = renderWithProviders(<FocusPage />, '/focus');

    await user.click(await screen.findByRole('button', { name: 'StudyFlow' }));
    await user.click(screen.getByRole('button', { name: 'Start focus' }));
    expect(await screen.findByRole('button', { name: 'Pause' })).toBeInTheDocument();

    serverTimer = null;
    await act(() => queryClient.invalidateQueries({ queryKey: queryKeys.activeTimer }));

    expect(await screen.findByText('The timer is complete. Confirm this segment before continuing.')).toBeInTheDocument();
    expect(screen.getByText('Focus #1').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByText('Focus #1').closest('li')?.querySelector('[data-study-flow-indicator="complete"]')).toBeInTheDocument();
    expect(mocks.completeTimer).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: 'Finish Segment' }));

    await waitFor(() => expect(mocks.confirmStudyFlowSegment).toHaveBeenCalledWith(
      'study-flow-1',
      0,
    ));
    expect(screen.getByRole('button', { name: 'Start short break' })).toBeInTheDocument();
    expect(screen.getByText('S-Break #1').closest('li')).toHaveAttribute('aria-current', 'step');
  });

  it('recovers StudyFlow progress with an active timer', async () => {
    window.localStorage.setItem('studyhub.studyFlow', JSON.stringify({
      isOpen: true,
      currentSegmentIndex: 2,
      isSegmentAwaitingFinish: true,
      sessionId: 'study-flow-1',
    }));
    mocks.getActiveTimer.mockResolvedValue(activeTimerFixture({
      study_flow_session_id: 'study-flow-1',
      study_flow_segment_index: 2,
    }));
    mocks.getStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: 'active',
      current_segment_index: 2,
      awaiting_confirmation: false,
      active_timer: activeTimerFixture({
        study_flow_session_id: 'study-flow-1',
        study_flow_segment_index: 2,
      }),
    });

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByRole('button', { name: 'StudyFlow' })).toBePressed();
    expect(screen.getByRole('button', { name: 'StudyFlow' })).toBeDisabled();
    expect(screen.getByText('Focus #2').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByRole('button', { name: 'Finish Segment' })).toBeInTheDocument();
  });

  it('recovers the next StudyFlow segment between timers', async () => {
    window.localStorage.setItem('studyhub.studyFlow', JSON.stringify({
      isOpen: true,
      currentSegmentIndex: 1,
      isSegmentAwaitingFinish: false,
      sessionId: 'study-flow-1',
    }));
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.getStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'StudyFlow session',
      category_id: null,
      status: 'active',
      current_segment_index: 1,
      awaiting_confirmation: false,
      active_timer: null,
    });

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByRole('button', { name: 'Start short break' })).toBeInTheDocument();
    expect(screen.getByText('S-Break #1').closest('li')).toHaveAttribute('aria-current', 'step');
  });

  it('recovers StudyFlow between timers from the server', async () => {
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.getActiveStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'Exam review flow',
      category_id: categoryFixture.id,
      status: 'active',
      current_segment_index: 1,
      awaiting_confirmation: false,
      active_timer: null,
    });
    mocks.getStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'Exam review flow',
      category_id: categoryFixture.id,
      status: 'active',
      current_segment_index: 1,
      awaiting_confirmation: false,
      active_timer: null,
    });

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByRole('button', { name: 'Start short break' })).toBeInTheDocument();
    expect(screen.getByText('S-Break #1').closest('li')).toHaveAttribute('aria-current', 'step');
    expect(screen.getByRole('button', { name: 'StudyFlow' })).toBePressed();
  });

  it('clears stale local progress when the server flow was canceled', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem('studyhub.studyFlow', JSON.stringify({
      isOpen: true,
      currentSegmentIndex: 2,
      isSegmentAwaitingFinish: true,
      sessionId: 'study-flow-1',
    }));
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.getStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'Canceled flow',
      category_id: null,
      status: 'cancelled',
      current_segment_index: 2,
      awaiting_confirmation: false,
      active_timer: null,
    });
    mocks.startTimer.mockResolvedValue(activeTimerFixture({
      study_flow_session_id: 'study-flow-2',
      study_flow_segment_index: 0,
    }));

    renderWithProviders(<FocusPage />, '/focus');

    const startButton = await screen.findByRole('button', { name: 'Start focus' });
    expect(screen.getByText('Focus #1').closest('li')).toHaveAttribute('aria-current', 'step');
    await user.click(startButton);
    await waitFor(() => expect(mocks.startTimer).toHaveBeenCalledWith(expect.objectContaining({
      study_flow_session_id: null,
      study_flow_segment_index: 0,
    })));
  });

  it('recovers an unconfirmed final segment from a completed server flow', async () => {
    window.localStorage.setItem('studyhub.studyFlow', JSON.stringify({
      isOpen: true,
      currentSegmentIndex: 5,
      isSegmentAwaitingFinish: true,
      sessionId: 'study-flow-1',
    }));
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.getStudyFlow.mockResolvedValue({
      session_id: 'study-flow-1',
      title: 'Completed flow',
      category_id: null,
      status: 'completed',
      current_segment_index: 5,
      awaiting_confirmation: true,
      active_timer: null,
    });

    renderWithProviders(<FocusPage />, '/focus');

    expect(await screen.findByText('The timer is complete. Confirm this segment before continuing.')).toBeInTheDocument();
    expect(screen.getByText('L-Break #1').closest('li')).toHaveAttribute('aria-current', 'step');
  });

  it('clears a persisted StudyFlow ID after its session was removed', async () => {
    window.localStorage.setItem('studyhub.studyFlow', JSON.stringify({
      isOpen: false,
      currentSegmentIndex: 6,
      isSegmentAwaitingFinish: false,
      sessionId: 'removed-flow',
    }));
    mocks.getActiveTimer.mockResolvedValue(null);
    mocks.getStudyFlow.mockRejectedValue(new ApiError('StudyFlow session not found', 404));

    renderWithProviders(<FocusPage />, '/focus');

    await waitFor(() => {
      expect(JSON.parse(window.localStorage.getItem('studyhub.studyFlow') ?? '{}')).toMatchObject({
        currentSegmentIndex: 0,
        sessionId: null,
      });
    });
    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: 'StudyFlow' }));
    expect(screen.getByRole('button', { name: 'Start focus' })).toBeInTheDocument();
  });
});
