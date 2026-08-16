import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { getCategories } from '../api/categories';
import type { TimerPhase } from '../api/contracts';
import { queryKeys } from '../api/queryKeys';
import { getPomodoroSettings } from '../api/settings';
import {
  cancelTimer,
  completeTimer,
  getActiveTimer,
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

type TimerCommand = 'pause' | 'resume' | 'complete' | 'cancel';
type OpenPanel = 'settings' | 'categories' | null;

export function FocusPage() {
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<TimerPhase>('focus');
  const [categoryId, setCategoryId] = useState('');
  const [title, setTitle] = useState('');
  const [openPanel, setOpenPanel] = useState<OpenPanel>(null);

  const settingsQuery = useQuery({ queryKey: queryKeys.settings, queryFn: getPomodoroSettings });
  const categoriesQuery = useQuery({ queryKey: queryKeys.categories, queryFn: () => getCategories(true) });
  const activeTimerQuery = useQuery({
    queryKey: queryKeys.activeTimer,
    queryFn: getActiveTimer,
    refetchInterval: (query) => query.state.data?.state === 'running' ? 5_000 : false,
  });

  const refreshTimerData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.activeTimer }),
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      queryClient.invalidateQueries({ queryKey: ['sessions'] }),
    ]);
    await queryClient.refetchQueries({ queryKey: queryKeys.activeTimer, type: 'active' });
  };

  const startMutation = useMutation({
    mutationFn: (payload: Parameters<typeof startTimer>[0]) => startTimer(payload),
    onSuccess: refreshTimerData,
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
    onSuccess: refreshTimerData,
  });

  const activeTimer = activeTimerQuery.data;
  const runningRemaining = useRemainingSeconds(
    activeTimer?.expected_end_at ?? null,
    activeTimer?.state === 'running',
  );

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

  if (settingsQuery.isLoading || categoriesQuery.isLoading || activeTimerQuery.isLoading) {
    return <div className={styles.page}><StatusBlock title="Recovering your focus state..." /></div>;
  }

  if (settingsQuery.isError || categoriesQuery.isError || activeTimerQuery.isError) {
    return (
      <div className={styles.page}>
        <StatusBlock
          tone="error"
          title="Focus is not ready"
          detail="Timer settings or categories could not be loaded. No timer has been started."
          action={<button className={styles.retry} onClick={() => void Promise.all([settingsQuery.refetch(), categoriesQuery.refetch(), activeTimerQuery.refetch()])}>Try again</button>}
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
    : selectedDuration * 60;
  const phaseLabel = phases.find((item) => item.id === displayPhase)?.label ?? 'Focus';
  const isBusy = startMutation.isPending || commandMutation.isPending;
  const commandError = startMutation.error ?? commandMutation.error;
  const activeCategory = categories.find((category) => category.id === activeTimer?.category_id);

  function handleStart() {
    startMutation.mutate({
      phase,
      category_id: phase === 'focus' ? categoryId || null : null,
      title: phase === 'focus' ? title.trim() || null : null,
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
        </div>
      </header>

      <div className={`${styles.layout} ${openPanel ? styles.withPanel : ''}`}>
        <section className={styles.timerStage} aria-labelledby="timer-heading">
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

          <div className={styles.timerCore}>
            <p className={styles.state}>{activeTimer ? activeTimer.state : 'ready'} / {phaseLabel}</p>
            <h2 id="timer-heading" className={styles.time} aria-live="off">{formatTimer(remainingSeconds)}</h2>
            <p className={styles.context}>
              {activeTimer?.title || activeCategory?.name || (displayPhase === 'focus' ? 'Choose your work below' : 'Step away for a moment')}
            </p>
          </div>

          {!activeTimer ? (
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
                {activeTimer.phase === 'focus' ? 'Finish session' : 'Finish break'}
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
