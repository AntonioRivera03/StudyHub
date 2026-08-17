import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { getCategories } from '../api/categories';
import { ApiError } from '../api/client';
import type { TimerPhase } from '../api/contracts';
import { queryKeys } from '../api/queryKeys';
import { getPomodoroSettings } from '../api/settings';
import {
  cancelTimer,
  confirmStudyFlowSegment,
  completeTimer,
  getActiveStudyFlow,
  getActiveTimer,
  getStudyFlow,
  pauseTimer,
  resumeTimer,
  startTimer,
} from '../api/timer';
import { CategoryManager } from '../components/CategoryManager';
import { SettingsPanel } from '../components/SettingsPanel';
import { StatusBlock } from '../components/StatusBlock';
import { useRemainingSeconds } from '../hooks/useRemainingSeconds';
import { formatTimer } from '../lib/time';
import styles from './FocusPage.module.css';

const phases: Array<{ id: TimerPhase; label: string; shortLabel: string }> = [
  { id: 'focus', label: 'Focus', shortLabel: 'Focus' },
  { id: 'short_break', label: 'Short break', shortLabel: 'Short' },
  { id: 'long_break', label: 'Long break', shortLabel: 'Long' },
];

const studyFlowSegments: Array<{ phase: TimerPhase; label: string }> = [
  { phase: 'focus', label: 'Focus #1' },
  { phase: 'short_break', label: 'S-Break #1' },
  { phase: 'focus', label: 'Focus #2' },
  { phase: 'short_break', label: 'S-Break #2' },
  { phase: 'focus', label: 'Focus #3' },
  { phase: 'long_break', label: 'L-Break #1' },
];

const studyFlowStorageKey = 'studyhub.studyFlow';

type StudyFlowState = {
  isOpen: boolean;
  currentSegmentIndex: number;
  isSegmentAwaitingFinish: boolean;
  sessionId: string | null;
};

function loadStudyFlowState(): StudyFlowState {
  const fallback: StudyFlowState = {
    isOpen: false,
    currentSegmentIndex: 0,
    isSegmentAwaitingFinish: false,
    sessionId: null,
  };
  if (typeof window === 'undefined') return fallback;

  try {
    const storedValue = window.localStorage.getItem(studyFlowStorageKey);
    if (!storedValue) return fallback;
    const parsed: unknown = JSON.parse(storedValue);
    if (!parsed || typeof parsed !== 'object') return fallback;
    const state = parsed as Record<string, unknown>;
    if (
      typeof state.isOpen !== 'boolean'
      || typeof state.currentSegmentIndex !== 'number'
      || !Number.isInteger(state.currentSegmentIndex)
      || state.currentSegmentIndex < 0
      || state.currentSegmentIndex > studyFlowSegments.length
      || typeof state.isSegmentAwaitingFinish !== 'boolean'
      || (
        state.sessionId !== undefined
        && state.sessionId !== null
        && typeof state.sessionId !== 'string'
      )
    ) return fallback;

    return {
      isOpen: state.isOpen,
      currentSegmentIndex: state.currentSegmentIndex,
      isSegmentAwaitingFinish: state.isSegmentAwaitingFinish,
      sessionId: typeof state.sessionId === 'string' ? state.sessionId : null,
    };
  } catch {
    return fallback;
  }
}

type TimerCommand = 'pause' | 'resume' | 'complete' | 'cancel';
type OpenPanel = 'settings' | 'categories' | null;

export function FocusPage() {
  const queryClient = useQueryClient();
  const [initialStudyFlowState] = useState(loadStudyFlowState);
  const initialStudyFlowPhase = studyFlowSegments[initialStudyFlowState.currentSegmentIndex]?.phase ?? 'focus';
  const [phase, setPhase] = useState<TimerPhase>(initialStudyFlowState.isOpen ? initialStudyFlowPhase : 'focus');
  const [categoryId, setCategoryId] = useState('');
  const [title, setTitle] = useState('');
  const [openPanel, setOpenPanel] = useState<OpenPanel>(null);
  const [isStudyFlowOpen, setIsStudyFlowOpen] = useState(initialStudyFlowState.isOpen);
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(initialStudyFlowState.currentSegmentIndex);
  const [isSegmentAwaitingFinish, setIsSegmentAwaitingFinish] = useState(initialStudyFlowState.isSegmentAwaitingFinish);
  const [studyFlowSessionId, setStudyFlowSessionId] = useState(initialStudyFlowState.sessionId);

  const settingsQuery = useQuery({ queryKey: queryKeys.settings, queryFn: getPomodoroSettings });
  const categoriesQuery = useQuery({ queryKey: queryKeys.categories, queryFn: () => getCategories(true) });
  const activeTimerQuery = useQuery({
    queryKey: queryKeys.activeTimer,
    queryFn: getActiveTimer,
    refetchInterval: (query) => query.state.data?.state === 'running' ? 5_000 : false,
  });
  const activeStudyFlowQuery = useQuery({
    queryKey: queryKeys.studyFlow(studyFlowSessionId),
    queryFn: () => studyFlowSessionId
      ? getStudyFlow(studyFlowSessionId)
      : getActiveStudyFlow(),
  });

  const refreshTimerData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.activeTimer }),
      queryClient.invalidateQueries({ queryKey: ['timer', 'study-flow'] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      queryClient.invalidateQueries({ queryKey: ['sessions'] }),
    ]);
    await queryClient.refetchQueries({ queryKey: queryKeys.activeTimer, type: 'active' });
    await queryClient.refetchQueries({
      queryKey: queryKeys.studyFlow(studyFlowSessionId),
      type: 'active',
    });
  };

  const startMutation = useMutation({
    mutationFn: (payload: Parameters<typeof startTimer>[0]) => startTimer(payload),
    onSuccess: async (timer) => {
      queryClient.setQueryData(queryKeys.activeTimer, timer);
      if (timer.study_flow_session_id) setStudyFlowSessionId(timer.study_flow_session_id);
      setIsSegmentAwaitingFinish(isStudyFlowOpen);
      await refreshTimerData();
    },
  });

  const commandMutation = useMutation({
    mutationFn: async ({ id, command }: { id: string; command: TimerCommand }) => {
      switch (command) {
        case 'pause': return pauseTimer(id);
        case 'resume': return resumeTimer(id);
        case 'complete': return completeTimer(id);
        case 'cancel': return cancelTimer(id);
      }
    },
    onSuccess: async (timer, { command }) => {
      await refreshTimerData();
      if (command === 'cancel' && timer.study_flow_session_id) {
        if (timer.state === 'completed') {
          setIsSegmentAwaitingFinish(true);
        } else {
          setCurrentSegmentIndex(0);
          setPhase('focus');
          setIsSegmentAwaitingFinish(false);
          setStudyFlowSessionId(null);
        }
      } else if (command === 'cancel') {
        setIsSegmentAwaitingFinish(false);
      }
      if (command === 'complete' && isStudyFlowOpen) finishStudyFlowSegment();
    },
  });

  const confirmSegmentMutation = useMutation({
    mutationFn: ({ sessionId, segmentIndex }: { sessionId: string; segmentIndex: number }) => (
      confirmStudyFlowSegment(sessionId, segmentIndex)
    ),
    onSuccess: async (studyFlow) => {
      applyStudyFlowState(studyFlow);
      await refreshTimerData();
    },
  });

  const activeTimer = activeTimerQuery.data;
  const persistedStudyFlowMissing = Boolean(
    studyFlowSessionId
    && activeStudyFlowQuery.error instanceof ApiError
    && activeStudyFlowQuery.error.status === 404,
  );
  const runningRemaining = useRemainingSeconds(
    activeTimer?.expected_end_at ?? null,
    activeTimer?.state === 'running',
  );

  useEffect(() => {
    try {
      window.localStorage.setItem(studyFlowStorageKey, JSON.stringify({
        isOpen: isStudyFlowOpen,
        currentSegmentIndex,
        isSegmentAwaitingFinish,
        sessionId: studyFlowSessionId,
      }));
    } catch {
      // The flow remains usable in-memory when browser storage is unavailable.
    }
  }, [currentSegmentIndex, isSegmentAwaitingFinish, isStudyFlowOpen, studyFlowSessionId]);

  useEffect(() => {
    if (
      !activeTimer?.study_flow_session_id
      || activeTimer.study_flow_segment_index === null
    ) return;
    const recoveredSegment = studyFlowSegments[activeTimer.study_flow_segment_index];
    if (!recoveredSegment) return;
    setStudyFlowSessionId(activeTimer.study_flow_session_id);
    setCurrentSegmentIndex(activeTimer.study_flow_segment_index);
    setPhase(recoveredSegment.phase);
    setIsSegmentAwaitingFinish(true);
    setIsStudyFlowOpen(true);
  }, [activeTimer]);

  useEffect(() => {
    const studyFlow = activeStudyFlowQuery.data;
    if (!activeStudyFlowQuery.isSuccess) return;
    if (!studyFlow) return;
    if (studyFlow.status === 'cancelled') {
      setStudyFlowSessionId(null);
      setCurrentSegmentIndex(0);
      setIsSegmentAwaitingFinish(false);
      setPhase('focus');
      return;
    }
    setStudyFlowSessionId(studyFlow.session_id);
    setCurrentSegmentIndex(studyFlow.current_segment_index);
    setIsSegmentAwaitingFinish(
      studyFlow.awaiting_confirmation || Boolean(studyFlow.active_timer),
    );
    setCategoryId(studyFlow.category_id ?? '');
    setTitle(studyFlow.title === 'StudyFlow session' ? '' : studyFlow.title);
    const currentSegment = studyFlowSegments[studyFlow.current_segment_index];
    if (currentSegment) setPhase(currentSegment.phase);
    setIsStudyFlowOpen(true);
  }, [
    activeStudyFlowQuery.data,
    activeStudyFlowQuery.isSuccess,
  ]);

  useEffect(() => {
    if (!persistedStudyFlowMissing) return;
    setStudyFlowSessionId(null);
    setCurrentSegmentIndex(0);
    setIsSegmentAwaitingFinish(false);
    setPhase('focus');
  }, [persistedStudyFlowMissing]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.code !== 'Space' || !activeTimer || commandMutation.isPending) return;
      const target = event.target;
      if (target instanceof HTMLElement && ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON', 'A'].includes(target.tagName)) return;
      event.preventDefault();
      commandMutation.mutate({
        id: activeTimer.id,
        command: activeTimer.state === 'running' ? 'pause' : 'resume',
      });
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTimer, commandMutation]);

  if (
    settingsQuery.isLoading
    || categoriesQuery.isLoading
    || activeTimerQuery.isLoading
  ) {
    return <div className={styles.page}><StatusBlock title="Recovering your focus state..." /></div>;
  }

  if (
    settingsQuery.isError
    || categoriesQuery.isError
    || activeTimerQuery.isError
    || (activeStudyFlowQuery.isError && !persistedStudyFlowMissing)
  ) {
    return (
      <div className={styles.page}>
        <StatusBlock
          tone="error"
          title="Focus is not ready"
          detail="Timer settings or categories could not be loaded. No timer has been started."
          action={<button className={styles.retry} onClick={() => void Promise.all([settingsQuery.refetch(), categoriesQuery.refetch(), activeTimerQuery.refetch(), activeStudyFlowQuery.refetch()])}>Try again</button>}
        />
      </div>
    );
  }

  const settings = settingsQuery.data;
  const categoryData = categoriesQuery.data;
  if (!settings || !categoryData) {
    return <div className={styles.page}><StatusBlock title="Recovering your focus state..." /></div>;
  }
  const categories = categoryData.filter((category) => !category.deleted_at);
  const displayPhase = activeTimer?.phase ?? phase;
  const selectedDuration = displayPhase === 'focus'
    ? settings.focus_minutes
    : displayPhase === 'short_break'
      ? settings.short_break_minutes
      : settings.long_break_minutes;
  const remainingSeconds = activeTimer
    ? activeTimer.state === 'running'
      ? runningRemaining
      : activeTimer.remaining_seconds
    : isStudyFlowOpen && isSegmentAwaitingFinish
      ? 0
      : selectedDuration * 60;
  const phaseLabel = phases.find((item) => item.id === displayPhase)?.label ?? 'Focus';
  const timerState = activeTimer
    ? activeTimer.state
    : isStudyFlowOpen && isSegmentAwaitingFinish
      ? 'complete'
      : 'ready';
  const isBusy = startMutation.isPending || commandMutation.isPending || confirmSegmentMutation.isPending;
  const commandError = startMutation.error ?? commandMutation.error ?? confirmSegmentMutation.error;
  const activeCategory = categories.find((category) => category.id === activeTimer?.category_id);

  function handleStart() {
    startMutation.mutate({
      phase,
      category_id: phase === 'focus' ? categoryId || null : null,
      title: phase === 'focus' ? title.trim() || null : null,
      ...(isStudyFlowOpen ? {
        study_flow_session_id: studyFlowSessionId,
        study_flow_segment_index: currentSegmentIndex,
      } : {}),
    });
  }

  function handleStudyFlowToggle() {
    if (isStudyFlowOpen) {
      setIsStudyFlowOpen(false);
      return;
    }

    const segmentIndex = currentSegmentIndex === studyFlowSegments.length ? 0 : currentSegmentIndex;
    const selectedSegment = studyFlowSegments[segmentIndex];
    if (!selectedSegment) return;
    setCurrentSegmentIndex(segmentIndex);
    if (currentSegmentIndex === studyFlowSegments.length) setStudyFlowSessionId(null);
    setPhase(selectedSegment.phase);
    setIsStudyFlowOpen(true);
  }

  function finishStudyFlowSegment() {
    setIsSegmentAwaitingFinish(false);
    const nextSegmentIndex = Math.min(currentSegmentIndex + 1, studyFlowSegments.length);
    setCurrentSegmentIndex(nextSegmentIndex);
    const nextSegment = studyFlowSegments[nextSegmentIndex];
    if (nextSegment) setPhase(nextSegment.phase);
  }

  function applyStudyFlowState(studyFlow: NonNullable<typeof activeStudyFlowQuery.data>) {
    if (studyFlow.status === 'cancelled') {
      setStudyFlowSessionId(null);
      setCurrentSegmentIndex(0);
      setIsSegmentAwaitingFinish(false);
      setPhase('focus');
      return;
    }
    setStudyFlowSessionId(studyFlow.session_id);
    setCurrentSegmentIndex(studyFlow.current_segment_index);
    setIsSegmentAwaitingFinish(
      studyFlow.awaiting_confirmation || Boolean(studyFlow.active_timer),
    );
    setCategoryId(studyFlow.category_id ?? '');
    setTitle(studyFlow.title === 'StudyFlow session' ? '' : studyFlow.title);
    const currentSegment = studyFlowSegments[studyFlow.current_segment_index];
    if (currentSegment) setPhase(currentSegment.phase);
    setIsStudyFlowOpen(true);
  }

  function handleFinishExpiredSegment() {
    if (!studyFlowSessionId) {
      finishStudyFlowSegment();
      return;
    }
    confirmSegmentMutation.mutate({
      sessionId: studyFlowSessionId,
      segmentIndex: currentSegmentIndex,
    });
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <p>FOCUS / LIVE</p>
          <h1>Keep one thing in view.</h1>
        </div>
        <div className={styles.utility}>
          <button onClick={() => setOpenPanel(openPanel === 'categories' ? null : 'categories')}>Categories</button>
          <button onClick={() => setOpenPanel(openPanel === 'settings' ? null : 'settings')}>Timer settings</button>
          <button
            className={isStudyFlowOpen ? styles.activeUtility : undefined}
            aria-pressed={isStudyFlowOpen}
            disabled={isBusy || Boolean(activeTimer) || isSegmentAwaitingFinish}
            onClick={handleStudyFlowToggle}
          >
            StudyFlow
          </button>
        </div>
      </header>

      {isStudyFlowOpen && (
        <section className={styles.studyFlow} aria-labelledby="study-flow-heading">
          <div className={styles.flowHeader}>
            <div>
              <p>STUDYFLOW / 6 SEGMENTS</p>
              <h2 id="study-flow-heading">A longer rhythm, mapped out.</h2>
            </div>
            <p>Finish each segment to unlock the next one.</p>
          </div>
          <ol className={styles.flowPipeline}>
            {studyFlowSegments.map((segment, index) => {
              const isComplete = index < currentSegmentIndex;
              const isCurrent = index === currentSegmentIndex;
              const isCurrentComplete = isCurrent && (
                (!activeTimer && isSegmentAwaitingFinish)
                || (Boolean(activeTimer) && remainingSeconds === 0)
              );
              const isCurrentInProgress = isCurrent && Boolean(activeTimer) && !isCurrentComplete;
              const indicatorState = isComplete
                ? 'past'
                : isCurrentComplete
                  ? 'complete'
                  : isCurrentInProgress
                    ? 'in-progress'
                    : isCurrent
                      ? 'not-started'
                      : null;
              const segmentStatus = isComplete || isCurrentComplete
                ? 'complete'
                : isCurrentInProgress
                  ? 'in progress'
                  : isCurrent
                    ? 'not started'
                    : 'queued';
              const duration = segment.phase === 'focus'
                ? settings.focus_minutes
                : segment.phase === 'short_break'
                  ? settings.short_break_minutes
                  : settings.long_break_minutes;

              return (
                <li
                  key={segment.label}
                  className={`${styles.flowSegment} ${isComplete ? styles.completedSegment : ''} ${isCurrent ? styles.currentSegment : ''}`}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  <span className={styles.segmentMarker}>
                    <span className={styles.segmentNumber}>{String(index + 1).padStart(2, '0')}</span>
                    {indicatorState && (
                      <span
                        className={`${styles.segmentDot} ${
                          indicatorState === 'past'
                            ? styles.pastSegmentDot
                            : indicatorState === 'complete'
                              ? styles.currentCompleteDot
                              : indicatorState === 'in-progress'
                                ? styles.currentProgressDot
                                : styles.currentNotStartedDot
                        }`}
                        data-study-flow-indicator={indicatorState}
                        aria-hidden="true"
                      />
                    )}
                  </span>
                  <strong>{segment.label}</strong>
                  <span>{duration} min / {segmentStatus}</span>
                </li>
              );
            })}
          </ol>
        </section>
      )}

      <div className={`${styles.layout} ${openPanel ? styles.withPanel : ''}`}>
        <section className={styles.timerStage} aria-labelledby="timer-heading">
          {!isStudyFlowOpen && (
            <div className={styles.phaseSelector} aria-label="Timer phase">
              {phases.map((item) => (
                <button
                  key={item.id}
                  className={displayPhase === item.id ? styles.selectedPhase : undefined}
                  aria-pressed={displayPhase === item.id}
                  disabled={Boolean(activeTimer)}
                  onClick={() => setPhase(item.id)}
                >
                  <span className={styles.fullPhase}>{item.label}</span>
                  <span className={styles.shortPhase}>{item.shortLabel}</span>
                </button>
              ))}
            </div>
          )}

          <div className={styles.timerCore}>
            <p className={styles.state}>{timerState} / {phaseLabel}</p>
            <h2 id="timer-heading" className={styles.time} aria-live="off">{formatTimer(remainingSeconds)}</h2>
            <p className={styles.context}>
              {activeTimer?.title || activeCategory?.name || (displayPhase === 'focus' ? 'Choose your work below' : 'Step away for a moment')}
            </p>
          </div>

          {!activeTimer && isStudyFlowOpen && isSegmentAwaitingFinish ? (
            <div className={styles.segmentGate}>
              <span role="status">The timer is complete. Confirm this segment before continuing.</span>
              <button className={styles.primary} onClick={handleFinishExpiredSegment} disabled={isBusy}>Finish Segment</button>
            </div>
          ) : !activeTimer && isStudyFlowOpen && currentSegmentIndex === studyFlowSegments.length ? (
            <div className={styles.flowFinished}>
              <strong>StudyFlow complete.</strong>
              <span>All six segments are finished. Close StudyFlow when you are ready to leave the sequence.</span>
            </div>
          ) : !activeTimer ? (
            <div className={styles.setup}>
              {phase === 'focus' && (
                <>
                  <label>
                    Category
                    <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
                      <option value="">Unsorted / No category</option>
                      {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
                    </select>
                  </label>
                  <label>
                    Focus title <span>(optional)</span>
                    <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="What does done look like?" />
                  </label>
                </>
              )}
              {categories.length === 0 && phase === 'focus' && (
                <button className={styles.categoryPrompt} onClick={() => setOpenPanel('categories')}>Create your first category</button>
              )}
              <button className={styles.primary} onClick={handleStart} disabled={isBusy}>
                {startMutation.isPending ? 'Starting...' : `Start ${phaseLabel.toLowerCase()}`}
              </button>
            </div>
          ) : (
            <div className={styles.controls}>
              {activeTimer.state === 'running' ? (
                <button className={styles.primary} onClick={() => commandMutation.mutate({ id: activeTimer.id, command: 'pause' })} disabled={isBusy}>Pause</button>
              ) : (
                <button className={styles.primary} onClick={() => commandMutation.mutate({ id: activeTimer.id, command: 'resume' })} disabled={isBusy}>Resume</button>
              )}
              <button onClick={() => commandMutation.mutate({ id: activeTimer.id, command: 'complete' })} disabled={isBusy}>
                {isStudyFlowOpen ? 'Finish Segment' : activeTimer.phase === 'focus' ? 'Finish session' : 'Finish break'}
              </button>
              <button className={styles.cancel} onClick={() => commandMutation.mutate({ id: activeTimer.id, command: 'cancel' })} disabled={isBusy}>Cancel</button>
              <span>Space to {activeTimer.state === 'running' ? 'pause' : 'resume'}</span>
            </div>
          )}

          {commandError && (
            <p className={styles.error} role="alert">
              {commandError instanceof Error ? commandError.message : 'The timer command failed. Please try again.'}
            </p>
          )}
        </section>

        {openPanel && (
          <aside className={styles.panelArea}>
            {openPanel === 'settings' && <SettingsPanel settings={settings} onClose={() => setOpenPanel(null)} />}
            {openPanel === 'categories' && <CategoryManager onClose={() => setOpenPanel(null)} />}
          </aside>
        )}
      </div>

      <footer className={styles.note}>
        <span aria-hidden="true">i</span>
        <p>The timer is recovered from StudyHub when this page reopens. A closed browser cannot play an end alert.</p>
      </footer>
    </div>
  );
}
