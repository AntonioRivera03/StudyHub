import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import {
  createCategory,
  deleteCategory,
  getCategories,
  restoreCategory,
  updateCategory,
} from '../api/categories';
import { ApiError } from '../api/client';
import { queryKeys } from '../api/queryKeys';
import { StatusBlock } from './StatusBlock';
import styles from './CategoryManager.module.css';

interface CategoryManagerProps {
  onClose: () => void;
}

type CategoryAction =
  | { kind: 'create'; name: string; color: string }
  | { kind: 'update'; id: string; name: string; color: string }
  | { kind: 'delete'; id: string }
  | { kind: 'restore'; id: string };

export function CategoryManager({ onClose }: CategoryManagerProps) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [color, setColor] = useState('#798186');
  const [showRemoved, setShowRemoved] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('#798186');
  const [validationError, setValidationError] = useState('');

  const categoriesQuery = useQuery({ queryKey: queryKeys.categories, queryFn: () => getCategories(true) });
  const mutation = useMutation({
    mutationFn: async (action: CategoryAction): Promise<void> => {
      switch (action.kind) {
        case 'create': await createCategory({ name: action.name, color: action.color }); break;
        case 'update': await updateCategory(action.id, { name: action.name, color: action.color }); break;
        case 'delete': await deleteCategory(action.id); break;
        case 'restore': await restoreCategory(action.id); break;
      }
    },
    onSuccess: async () => {
      setName('');
      setEditingId(null);
      setValidationError('');
      await queryClient.invalidateQueries({ queryKey: queryKeys.categories });
    },
  });

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setValidationError('Category name cannot be empty.');
      return;
    }
    mutation.mutate({ kind: 'create', name: name.trim(), color });
  }

  function beginEdit(id: string, currentName: string, currentColor: string) {
    setEditingId(id);
    setEditName(currentName);
    setEditColor(currentColor);
  }

  function saveEdit(id: string) {
    if (!editName.trim()) {
      setValidationError('Category name cannot be empty.');
      return;
    }
    mutation.mutate({ kind: 'update', id, name: editName.trim(), color: editColor });
  }

  const visibleCategories = (categoriesQuery.data ?? []).filter((category) => showRemoved || !category.deleted_at);

  return (
    <section className={styles.panel} aria-labelledby="categories-title">
      <div className={styles.heading}>
        <div>
          <p>Organize</p>
          <h2 id="categories-title">Categories</h2>
        </div>
        <button type="button" onClick={onClose}>Close</button>
      </div>

      <form className={styles.createForm} onSubmit={handleCreate}>
        <label>
          New category
          <span className={styles.createFields}>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name" />
            <input className={styles.color} type="color" value={color} onChange={(event) => setColor(event.target.value)} aria-label="New category color" />
            <button type="submit" disabled={mutation.isPending}>Add</button>
          </span>
        </label>
      </form>

      <label className={styles.removedToggle}>
        <input type="checkbox" checked={showRemoved} onChange={(event) => setShowRemoved(event.target.checked)} />
        View removed categories
      </label>

      {(validationError || mutation.isError) && (
        <p className={styles.error} role="alert">
          {validationError || (mutation.error instanceof ApiError
            ? mutation.error.message
            : 'That category change could not be saved.')}
        </p>
      )}

      {categoriesQuery.isLoading && <StatusBlock title="Loading categories..." />}
      {categoriesQuery.isError && <StatusBlock tone="error" title="Categories are unavailable" />}
      {categoriesQuery.isSuccess && visibleCategories.length === 0 && (
        <StatusBlock title={showRemoved ? 'No categories found' : 'No active categories'} detail="Add one above to label focused work." />
      )}

      <div className={styles.list}>
        {visibleCategories.map((category) => (
          <div className={`${styles.row} ${category.deleted_at ? styles.removed : ''}`} key={category.id}>
            {editingId === category.id ? (
              <>
                <input className={styles.editName} aria-label={`Edit ${category.name} name`} value={editName} onChange={(event) => setEditName(event.target.value)} />
                <input className={styles.color} type="color" aria-label={`Edit ${category.name} color`} value={editColor} onChange={(event) => setEditColor(event.target.value)} />
                <button onClick={() => saveEdit(category.id)} disabled={mutation.isPending}>Save</button>
                <button onClick={() => setEditingId(null)}>Cancel</button>
              </>
            ) : (
              <>
                <span className={styles.swatch} style={{ backgroundColor: category.color ?? '#798186' }} aria-hidden="true" />
                <span className={styles.name}>{category.name}</span>
                {category.deleted_at ? (
                  <button onClick={() => mutation.mutate({ kind: 'restore', id: category.id })} disabled={mutation.isPending}>Restore</button>
                ) : (
                  <>
                    <button onClick={() => beginEdit(category.id, category.name, category.color ?? '#798186')}>Edit</button>
                    <button className={styles.delete} onClick={() => mutation.mutate({ kind: 'delete', id: category.id })} disabled={mutation.isPending}>Remove</button>
                  </>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
