import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardSummary } from '../api/dashboard';
import { queryKeys } from '../api/queryKeys';
import { ManualSessionForm } from '../components/ManualSessionForm';
import { SessionHistory } from '../components/SessionHistory';
import { StatusBlock } from '../components/StatusBlock';
import { formatDuration, formatTimer, getGreeting } from '../lib/time';
import styles from './TodayPage.module.css';

export function TodayPage() {
  const [showManualForm, setShowManualForm] = useState(false);
  const now = new Date();
  const timezoneOffsetMinutes = now.getTimezoneOffset();
  const summaryQuery = useQuery({
    queryKey: queryKeys.dashboard(timezoneOffsetMinutes),
    queryFn: () => getDashboardSummary(timezoneOffsetMinutes),
  });

  if (summaryQuery.isLoading) {
    return <div className={styles.page}><StatusBlock title="Preparing today..." /></div>;
  }

  if (summaryQuery.isError) {
    return (
      <div className={styles.page}>
        <StatusBlock
          tone="error"
          title="Today could not be loaded"
          detail="StudyHub could not reach the summary service."
          action={<button className={styles.retry} onClick={() => void summaryQuery.refetch()}>Try again</button>}
        />
      </div>
    );
  }

  const summary = summaryQuery.data;
  if (!summary) {
    return <div className={styles.page}><StatusBlock title="Preparing today..." /></div>;
  }
  const activeTimer = summary.active_timer;
  const isEmpty = summary.today_completed_session_count === 0 && summary.recent_sessions.length === 0;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <p className={styles.eyebrow}>{now.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
        <h1>{getGreeting(now.getHours())}</h1>
        <p className={styles.intro}>A clear record of the work in front of you.</p>
      </header>

      <section className={styles.metrics} aria-label="Today's summary">
        <div>
          <span>Completed focus</span>
          <strong>{formatDuration(summary.today_completed_focus_minutes * 60)}</strong>
        </div>
        <div>
          <span>Sessions</span>
          <strong>{summary.today_completed_session_count}</strong>
        </div>
        <p className={styles.metricNote}>Today / local time</p>
      </section>

      {activeTimer && (
        <section className={styles.active} aria-label="Active timer">
          <div>
            <span className={styles.live}>{activeTimer.state}</span>
            <h2>{activeTimer.title || (activeTimer.phase === 'focus' ? 'Focused work' : 'Break')}</h2>
            <p>{activeTimer.phase.replace('_', ' ')}</p>
          </div>
          <div className={styles.activeAction}>
            {activeTimer.state === 'paused' && (
              <span>{formatTimer(activeTimer.remaining_seconds)}</span>
            )}
            <Link to="/focus">Continue timer</Link>
          </div>
        </section>
      )}

      {isEmpty && !activeTimer && (
        <section className={styles.firstSession}>
          <p className={styles.firstIndex}>01 / BEGIN</p>
          <h2>Make one interval count.</h2>
          <p>Choose what you are working on, start a focus timer, and this page will keep the record.</p>
          <Link to="/focus">Start focusing</Link>
        </section>
      )}

      <section className={styles.history} aria-labelledby="history-title">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.sectionIndex}>LOG / TODAY</p>
            <h2 id="history-title">Recent sessions</h2>
          </div>
          <button onClick={() => setShowManualForm((visible) => !visible)}>
            {showManualForm ? 'Cancel entry' : 'Add manual session'}
          </button>
        </div>
        {showManualForm && <ManualSessionForm onClose={() => setShowManualForm(false)} />}
        <SessionHistory />
      </section>
    </div>
  );
}
