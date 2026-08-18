import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { getCategories } from '../api/categories';
import { ApiError } from '../api/client';
import type { FlashcardDeck, UpdateDeckRequest } from '../api/contracts';
import {
  createDeck,
  deleteDeck,
  getDecks,
  restoreDeck,
  updateDeck,
} from '../api/decks';
import { queryKeys } from '../api/queryKeys';
import { getActiveReview } from '../api/reviews';
import { StatusBlock } from '../components/StatusBlock';
import styles from './FlashcardsPage.module.css';

type DeckAction =
  | { kind: 'create'; name: string; description: string | null; categoryId: string | null }
  | { kind: 'update'; id: string; payload: UpdateDeckRequest }
  | { kind: 'delete'; id: string }
  | { kind: 'restore'; id: string };

export function FlashcardsPage() {
  const queryClient = useQueryClient();
  const [showRemoved, setShowRemoved] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editCategoryId, setEditCategoryId] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState('');

  const decksQuery = useQuery({
    queryKey: queryKeys.decks(showRemoved),
    queryFn: () => getDecks(showRemoved),
  });
  const categoriesQuery = useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => getCategories(true),
  });
  const activeReviewQuery = useQuery({
    queryKey: queryKeys.activeReview,
    queryFn: getActiveReview,
  });

  const mutation = useMutation({
    mutationFn: async (action: DeckAction): Promise<void> => {
      switch (action.kind) {
        case 'create':
          await createDeck({
            name: action.name,
            description: action.description,
            category_id: action.categoryId,
          });
          break;
        case 'update':
          await updateDeck(action.id, action.payload);
          break;
        case 'delete':
          await deleteDeck(action.id);
          break;
        case 'restore':
          await restoreDeck(action.id);
          break;
      }
    },
    onSuccess: async () => {
      setName('');
      setDescription('');
      setCategoryId('');
      setShowCreate(false);
      setEditingId(null);
      setConfirmDeleteId(null);
      setValidationError('');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['decks'] }),
        queryClient.invalidateQueries({ queryKey: queryKeys.activeReview }),
      ]);
    },
  });

  const categories = categoriesQuery.data ?? [];
  const activeCategories = categories.filter((category) => !category.deleted_at);
  const decks = decksQuery.data ?? [];
  const isLoading = decksQuery.isLoading;
  const hasLoadError = decksQuery.isError;

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setValidationError('Deck name cannot be empty.');
      return;
    }
    if (trimmedName.length > 160 || description.length > 2_000) {
      setValidationError('Use at most 160 characters for the name and 2,000 for the description.');
      return;
    }
    setValidationError('');
    mutation.mutate({
      kind: 'create',
      name: trimmedName,
      description: description.trim() ? description : null,
      categoryId: categoryId || null,
    });
  }

  function beginEdit(deck: FlashcardDeck) {
    setEditingId(deck.id);
    setEditName(deck.name);
    setEditDescription(deck.description ?? '');
    setEditCategoryId(deck.category_id ?? '');
    setValidationError('');
    mutation.reset();
  }

  function saveEdit(deck: FlashcardDeck) {
    const trimmedName = editName.trim();
    if (!trimmedName) {
      setValidationError('Deck name cannot be empty.');
      return;
    }
    if (trimmedName.length > 160 || editDescription.length > 2_000) {
      setValidationError('Use at most 160 characters for the name and 2,000 for the description.');
      return;
    }
    const payload: UpdateDeckRequest = {
      name: trimmedName,
      description: editDescription.trim() ? editDescription : null,
    };
    if (editCategoryId !== (deck.category_id ?? '')) {
      payload.category_id = editCategoryId || null;
    }
    setValidationError('');
    mutation.mutate({ kind: 'update', id: deck.id, payload });
  }

  function categoryName(deck: FlashcardDeck) {
    const category = categories.find((item) => item.id === deck.category_id);
    if (!category) return 'Unsorted';
    return category.deleted_at ? `${category.name} (removed)` : category.name;
  }

  function requestDelete(id: string) {
    setConfirmDeleteId(id);
    setEditingId(null);
    setValidationError('');
    mutation.reset();
  }

  if (isLoading) {
    return <div className={styles.page}><StatusBlock title="Gathering your decks..." /></div>;
  }

  if (hasLoadError) {
    return (
      <div className={styles.page}>
        <StatusBlock
          tone="error"
          title="Flashcards could not be loaded"
          detail="No changes were made. Try requesting your decks again."
          action={(
            <button className={styles.retry} onClick={() => void decksQuery.refetch()}>
              Try again
            </button>
          )}
        />
      </div>
    );
  }

  const activeReview = activeReviewQuery.data;
  const mutationMessage = mutation.error instanceof ApiError
    ? mutation.error.message
    : 'That deck change could not be saved. Please try again.';

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <p>FLASHCARDS / DECKS</p>
          <h1>Keep recall within reach.</h1>
          <span>Build cards, notice what is due, and review one queue at a time.</span>
        </div>
        <button
          className={styles.primary}
          onClick={() => {
            setShowCreate((visible) => !visible);
            setEditingId(null);
            setValidationError('');
            mutation.reset();
          }}
        >
          {showCreate ? 'Close form' : 'New deck'}
        </button>
      </header>

      {activeReview && (
        <section className={styles.resume} aria-labelledby="active-review-heading">
          <div>
            <p>Review in progress</p>
            <h2 id="active-review-heading">
              {decks.find((deck) => deck.id === activeReview.session.deck_id)?.name ?? 'Current review'}
            </h2>
            <span>{activeReview.reviewed_card_count} reviewed / {activeReview.remaining_due_card_count} remaining</span>
          </div>
          <Link to={`/flashcards/review/${activeReview.session.id}`}>Resume review</Link>
        </section>
      )}

      {showCreate && (
        <form className={styles.deckForm} onSubmit={handleCreate} aria-label="Create deck">
          <div className={styles.formHeading}>
            <div>
              <p>NEW / DECK</p>
              <h2>Start with a clear scope.</h2>
            </div>
            <span>Cards inherit this deck's category.</span>
          </div>
          <label>
            Deck name
            <input
              value={name}
              maxLength={160}
              onChange={(event) => setName(event.target.value)}
              autoFocus
              required
            />
          </label>
          <label>
            Description <span>optional</span>
            <textarea
              value={description}
              maxLength={2_000}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <label>
            Category
            <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              <option value="">Unsorted</option>
              {activeCategories.map((category) => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </label>
          <button className={styles.primary} type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create deck'}
          </button>
        </form>
      )}

      {(validationError || mutation.isError) && (
        <p className={styles.error} role="alert">{validationError || mutationMessage}</p>
      )}

      <section className={styles.library} aria-labelledby="deck-library-heading">
        <div className={styles.toolbar}>
          <div>
            <p>LIBRARY / {String(decks.length).padStart(2, '0')}</p>
            <h2 id="deck-library-heading">Your decks</h2>
          </div>
          <label className={styles.removedToggle}>
            <input
              type="checkbox"
              checked={showRemoved}
              onChange={(event) => setShowRemoved(event.target.checked)}
            />
            Include removed
          </label>
        </div>

        {decks.length === 0 ? (
          <StatusBlock
            title={showRemoved ? 'No decks found' : 'No active decks yet'}
            detail="Create a deck, then add the first question and answer."
          />
        ) : (
          <div className={styles.deckList}>
            {decks.map((deck, index) => (
              <article
                className={`${styles.deck} ${deck.deleted_at ? styles.removed : ''}`}
                key={deck.id}
              >
                {editingId === deck.id ? (
                  <div className={styles.editForm}>
                    <p>Editing {deck.name}</p>
                    <label>
                      Deck name
                      <input
                        value={editName}
                        maxLength={160}
                        onChange={(event) => setEditName(event.target.value)}
                      />
                    </label>
                    <label>
                      Description <span>optional</span>
                      <textarea
                        value={editDescription}
                        maxLength={2_000}
                        onChange={(event) => setEditDescription(event.target.value)}
                      />
                    </label>
                    <label>
                      Category
                      <select value={editCategoryId} onChange={(event) => setEditCategoryId(event.target.value)}>
                        <option value="">Unsorted</option>
                        {deck.category_id && !activeCategories.some((item) => item.id === deck.category_id) && (
                          <option value={deck.category_id} disabled>{categoryName(deck)}</option>
                        )}
                        {activeCategories.map((category) => (
                          <option key={category.id} value={category.id}>{category.name}</option>
                        ))}
                      </select>
                    </label>
                    <div className={styles.formActions}>
                      <button className={styles.primary} onClick={() => saveEdit(deck)} disabled={mutation.isPending}>Save deck</button>
                      <button onClick={() => setEditingId(null)}>Cancel</button>
                    </div>
                  </div>
                ) : confirmDeleteId === deck.id ? (
                  <div className={styles.confirm} aria-live="polite">
                    <div>
                      <h3 id={`remove-${deck.id}`}>Remove {deck.name}?</h3>
                      <p>Its cards stay stored but leave browse and review queues. You can restore the deck later.</p>
                    </div>
                    <div className={styles.formActions}>
                      <button
                        className={styles.destructive}
                        disabled={mutation.isPending}
                        onClick={() => mutation.mutate({ kind: 'delete', id: deck.id })}
                      >
                        {mutation.isPending ? 'Removing...' : 'Remove deck'}
                      </button>
                      <button onClick={() => setConfirmDeleteId(null)}>Keep deck</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className={styles.deckIndex} aria-hidden="true">{String(index + 1).padStart(2, '0')}</div>
                    <div className={styles.deckBody}>
                      <div className={styles.deckTitle}>
                        <div>
                          <p>{categoryName(deck)}</p>
                          <h3><Link to={`/flashcards/decks/${deck.id}`}>{deck.name}</Link></h3>
                        </div>
                        <span>{deck.deleted_at ? 'Removed' : deck.due_card_count > 0 ? `${deck.due_card_count} due` : 'Queue clear'}</span>
                      </div>
                      {deck.description && <p className={styles.description}>{deck.description}</p>}
                      <div className={styles.deckMeta}>
                        <span>{deck.active_card_count} {deck.active_card_count === 1 ? 'card' : 'cards'}</span>
                        <span>{deck.due_card_count} due now</span>
                        <span>Updated {new Date(deck.updated_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className={styles.deckActions}>
                      <Link to={`/flashcards/decks/${deck.id}`}>{deck.deleted_at ? 'View' : 'Open'}</Link>
                      {deck.deleted_at ? (
                        <button
                          disabled={mutation.isPending}
                          onClick={() => mutation.mutate({ kind: 'restore', id: deck.id })}
                        >
                          Restore
                        </button>
                      ) : (
                        <>
                          <button onClick={() => beginEdit(deck)}>Edit</button>
                          <button
                            className={styles.removeButton}
                            disabled={activeReview?.session.deck_id === deck.id}
                            title={activeReview?.session.deck_id === deck.id
                              ? 'Complete or abandon this deck review before removing it'
                              : undefined}
                            onClick={() => requestDelete(deck.id)}
                          >
                            Remove
                          </button>
                        </>
                      )}
                    </div>
                  </>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
