import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { getCategories } from '../api/categories';
import { ApiError } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { createSession } from '../api/sessions';
import { toLocalDateTimeInput } from '../lib/time';
import styles from './ManualSessionForm.module.css';

interface ManualSessionFormProps {
  onClose: () => void;
}

export function ManualSessionForm({ onClose }: ManualSessionFormProps) {
  const queryClient = useQueryClient();
  const now = new Date();
  const [title, setTitle] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [startedAt, setStartedAt] = useState(() => toLocalDateTimeInput(new Date(now.getTime() - 25 * 60_000)));
  const [endedAt, setEndedAt] = useState(() => toLocalDateTimeInput(now));
  const [notes, setNotes] = useState('');
  const [validationError, setValidationError] = useState('');

  const categoriesQuery = useQuery({ queryKey: queryKeys.categories, queryFn: () => getCategories(true) });
  const categories = (categoriesQuery.data ?? []).filter((category) => !category.deleted_at);

  const createMutation = useMutation({
    mutationFn: (payload: Parameters<typeof createSession>[0]) => createSession(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['sessions'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]);
      onClose();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const start = new Date(startedAt);
    const end = new Date(endedAt);
    if (!title.trim()) {
      setValidationError('Add a short title for this session.');
      return;
    }
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
      setValidationError('End time must be later than start time.');
      return;
    }
    setValidationError('');
    createMutation.mutate({
      title: title.trim(),
      category_id: categoryId || null,
      started_at: start.toISOString(),
      ended_at: end.toISOString(),
      notes: notes.trim() || null,
    });
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} aria-label="Add a manual session">
      <div className={styles.formHeading}>
        <div>
          <h3>Manual session</h3>
          <p>Record focused work completed away from the timer.</p>
        </div>
        <button type="button" className={styles.close} onClick={onClose}>Close</button>
      </div>

      <div className={styles.grid}>
        <label className={styles.wide}>
          Title
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Review chapter four" />
        </label>
        <label>
          Category
          <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="">Unsorted</option>
            {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
        <label>
          Started
          <input type="datetime-local" value={startedAt} onChange={(event) => setStartedAt(event.target.value)} />
        </label>
        <label>
          Ended
          <input type="datetime-local" value={endedAt} onChange={(event) => setEndedAt(event.target.value)} />
        </label>
        <label className={styles.wide}>
          Notes <span>(optional)</span>
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="What moved forward?" />
        </label>
      </div>

      {(validationError || createMutation.isError) && (
        <p className={styles.error} role="alert">
          {validationError || (createMutation.error instanceof ApiError
            ? createMutation.error.message
            : 'The session could not be saved. Please try again.')}
        </p>
      )}

      <div className={styles.actions}>
        <button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? 'Saving...' : 'Save session'}
        </button>
      </div>
    </form>
  );
}
