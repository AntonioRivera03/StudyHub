import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { getCategories } from '../api/categories';
import { deleteSession, getSessions, restoreSession } from '../api/sessions';
import { queryKeys } from '../api/queryKeys';
import { formatDuration, formatSessionTime, getSessionDurationSeconds } from '../lib/time';
import { StatusBlock } from './StatusBlock';
import styles from './SessionHistory.module.css';

export function SessionHistory() {
  const queryClient = useQueryClient();
  const [showRemoved, setShowRemoved] = useState(false);
  const sessionsQuery = useQuery({
    queryKey: queryKeys.sessions(showRemoved),
    queryFn: () => getSessions({ include_deleted: showRemoved }),
  });
  const categoriesQuery = useQuery({ queryKey: queryKeys.categories, queryFn: () => getCategories(true) });

  const changeState = useMutation({
    mutationFn: async ({ id, restore }: { id: string; restore: boolean }): Promise<void> => {
      if (restore) await restoreSession(id);
      else await deleteSession(id);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['sessions'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]);
    },
  });

  if (sessionsQuery.isLoading) {
    return <StatusBlock title="Loading session history..." />;
  }

  if (sessionsQuery.isError) {
    return (
      <StatusBlock
        tone="error"
        title="Session history is unavailable"
        detail="Your summary is still safe. Try loading these rows again."
        action={<button className={styles.retry} onClick={() => void sessionsQuery.refetch()}>Try again</button>}
      />
    );
  }

  const sessions = (sessionsQuery.data ?? []).slice(0, 20);
  const categories = categoriesQuery.data ?? [];

  return (
    <div>
      <div className={styles.toolbar}>
        <p>{sessions.length} recent {sessions.length === 1 ? 'session' : 'sessions'}</p>
        <label className={styles.removedToggle}>
          <input
            type="checkbox"
            checked={showRemoved}
            onChange={(event) => setShowRemoved(event.target.checked)}
          />
          Include removed
        </label>
      </div>

      {changeState.isError && (
        <p className={styles.error} role="alert">That session could not be updated. Please try again.</p>
      )}

      {sessions.length === 0 ? (
        <StatusBlock title="No sessions recorded yet" detail="Finished focus timers and manual entries will appear here." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Session</th>
                <th>Category</th>
                <th>Time</th>
                <th>Duration</th>
                <th>Source</th>
                <th>Status</th>
                <th><span className={styles.visuallyHidden}>Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => {
                const category = categories.find((item) => item.id === session.category_id);
                const durationSeconds = session.status === 'active'
                  ? getSessionDurationSeconds(session.started_at, session.ended_at)
                  : session.duration_seconds;
                return (
                  <tr key={session.id} className={session.deleted_at ? styles.removed : undefined}>
                    <td>
                      <span className={styles.sessionTitle}>{session.title || 'Untitled focus'}</span>
                      {session.notes && <span className={styles.notes}>{session.notes}</span>}
                    </td>
                    <td>
                      <span className={styles.category}>
                        {category && (
                          <span className={styles.dot} style={{ backgroundColor: category.color ?? '#798186' }} aria-hidden="true" />
                        )}
                        {category?.name ?? 'Unsorted'}
                      </span>
                    </td>
                    <td className={styles.mono}>{formatSessionTime(session.started_at, session.ended_at)}</td>
                    <td className={styles.mono}>{formatDuration(durationSeconds)}</td>
                    <td>{session.source}</td>
                    <td>{session.deleted_at ? 'removed' : session.status}</td>
                    <td>
                      <button
                        className={styles.rowAction}
                        disabled={changeState.isPending}
                        onClick={() => changeState.mutate({ id: session.id, restore: Boolean(session.deleted_at) })}
                      >
                        {session.deleted_at ? 'Restore' : 'Remove'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
