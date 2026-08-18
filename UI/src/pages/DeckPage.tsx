import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getCategories } from '../api/categories';
import {
  createCard,
  deleteCard,
  getCards,
  restoreCard,
  updateCard,
} from '../api/cards';
import { ApiError } from '../api/client';
import type { CreateCardRequest, Flashcard, UpdateCardRequest } from '../api/contracts';
import { getDeck, restoreDeck } from '../api/decks';
import { queryKeys } from '../api/queryKeys';
import { getActiveReview, startReview } from '../api/reviews';
import { MarkdownContent } from '../components/MarkdownContent';
import { StatusBlock } from '../components/StatusBlock';
import styles from './DeckPage.module.css';

type CardAction =
  | { kind: 'create'; payload: CreateCardRequest }
  | { kind: 'update'; id: string; payload: UpdateCardRequest }
  | { kind: 'delete'; id: string }
  | { kind: 'restore'; id: string }
  | { kind: 'restore-deck' };

function isValidPosition(value: string): boolean {
  if (!value) return true;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 0;
}

export function DeckPage() {
  const { deckId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showRemoved, setShowRemoved] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showReviewSetup, setShowReviewSetup] = useState(false);
  const [front, setFront] = useState('');
  const [back, setBack] = useState('');
  const [position, setPosition] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFront, setEditFront] = useState('');
  const [editBack, setEditBack] = useState('');
  const [editPosition, setEditPosition] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [validationError, setValidationError] = useState('');

  const deckQuery = useQuery({
    queryKey: queryKeys.deck(deckId, true),
    queryFn: () => getDeck(deckId, true),
    enabled: Boolean(deckId),
  });
  const includeDeletedCards = showRemoved || Boolean(deckQuery.data?.deleted_at);
  const cardsQuery = useQuery({
    queryKey: queryKeys.cards(deckId, includeDeletedCards),
    queryFn: () => getCards(deckId, includeDeletedCards),
    enabled: Boolean(deckId) && deckQuery.isSuccess,
  });
  const categoriesQuery = useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => getCategories(true),
  });
  const activeReviewQuery = useQuery({
    queryKey: queryKeys.activeReview,
    queryFn: getActiveReview,
  });
  const activeReview = activeReviewQuery.data;
  const activeReviewIsThisDeck = activeReview != null
    && deckQuery.data !== undefined
    && activeReview.session.deck_id === deckQuery.data.id;

  const refreshDeck = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['decks'] }),
      queryClient.invalidateQueries({ queryKey: queryKeys.deck(deckId, true) }),
      queryClient.invalidateQueries({ queryKey: ['decks', deckId, 'cards'] }),
      queryClient.invalidateQueries({ queryKey: queryKeys.dueCards(deckId) }),
    ]);
  };

  const mutation = useMutation({
    mutationFn: async (action: CardAction): Promise<void> => {
      switch (action.kind) {
        case 'create':
          await createCard(deckId, action.payload);
          break;
        case 'update':
          await updateCard(action.id, action.payload);
          break;
        case 'delete':
          await deleteCard(action.id);
          break;
        case 'restore':
          await restoreCard(action.id);
          break;
        case 'restore-deck':
          await restoreDeck(deckId);
          break;
      }
    },
    onSuccess: async (_, action) => {
      setEditingId(null);
      setConfirmDeleteId(null);
      setValidationError('');
      if (action.kind === 'create') {
        setFront('');
        setBack('');
        setPosition('');
        setShowCreate(false);
      }
      await refreshDeck();
    },
  });

  const startMutation = useMutation({
    mutationFn: () => startReview({ deck_id: deckId }),
    onSuccess: async (progress) => {
      queryClient.setQueryData(queryKeys.review(progress.session.id), progress);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.activeReview }),
        refreshDeck(),
      ]);
      void navigate(`/flashcards/review/${progress.session.id}`);
    },
  });

  function runCardAction(action: CardAction) {
    if (activeReviewIsThisDeck) return;
    mutation.mutate(action);
  }

  function validateCard(frontSource: string, backSource: string, positionValue: string) {
    if (!frontSource.trim() || !backSource.trim()) {
      return 'Both card faces need at least one visible character.';
    }
    if (frontSource.length > 20_000 || backSource.length > 20_000) {
      return 'Each card face must be 20,000 characters or fewer.';
    }
    if (!isValidPosition(positionValue)) {
      return 'Position must be a whole number of zero or greater.';
    }
    return '';
  }

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = validateCard(front, back, position);
    if (message) {
      setValidationError(message);
      return;
    }
    setValidationError('');
    runCardAction({
      kind: 'create',
      payload: {
        front_markdown: front,
        back_markdown: back,
        ...(position ? { position: Number(position) } : {}),
      },
    });
  }

  function beginEdit(card: Flashcard) {
    setEditingId(card.id);
    setEditFront(card.front_markdown);
    setEditBack(card.back_markdown);
    setEditPosition(String(card.position));
    setConfirmDeleteId(null);
    setValidationError('');
    mutation.reset();
  }

  function saveEdit(card: Flashcard) {
    if (activeReviewIsThisDeck) return;
    const message = validateCard(editFront, editBack, editPosition);
    if (message) {
      setValidationError(message);
      return;
    }
    setValidationError('');
    runCardAction({
      kind: 'update',
      id: card.id,
      payload: {
        front_markdown: editFront,
        back_markdown: editBack,
        ...(editPosition ? { position: Number(editPosition) } : {}),
      },
    });
  }

  const isLoading = deckQuery.isLoading
    || cardsQuery.isLoading;
  const hasLoadError = deckQuery.isError
    || cardsQuery.isError;

  if (isLoading) {
    return <div className={styles.page}><StatusBlock title="Opening this deck..." /></div>;
  }

  if (hasLoadError || !deckQuery.data) {
    return (
      <div className={styles.page}>
        <Link className={styles.backLink} to="/flashcards">Back to decks</Link>
        <StatusBlock
          tone="error"
          title="This deck could not be opened"
          detail="It may no longer exist, or its cards are temporarily unavailable."
          action={<button className={styles.retry} onClick={() => void Promise.all([deckQuery.refetch(), cardsQuery.refetch()])}>Try again</button>}
        />
      </div>
    );
  }

  const deck = deckQuery.data;
  const cards = cardsQuery.data ?? [];
  const category = (categoriesQuery.data ?? []).find((item) => item.id === deck.category_id);
  const categoryLabel = !category
    ? 'Unsorted'
    : category.deleted_at
      ? `${category.name} (removed)`
      : category.name;
  const requestError = mutation.error ?? startMutation.error;
  const requestErrorMessage = requestError instanceof ApiError
    ? requestError.message
    : 'That change could not be saved. Please try again.';

  return (
    <div className={styles.page}>
      <Link className={styles.backLink} to="/flashcards">Back to decks</Link>
      <header className={styles.header}>
        <div>
          <p>DECK / {deck.deleted_at ? 'REMOVED' : `${deck.due_card_count} DUE`}</p>
          <h1>{deck.name}</h1>
          <span>{deck.description ?? 'No description yet.'}</span>
        </div>
        <div className={styles.headerStats} aria-label="Deck summary">
          <div><strong>{deck.active_card_count}</strong><span>cards</span></div>
          <div><strong>{deck.due_card_count}</strong><span>due now</span></div>
        </div>
      </header>

      <section className={styles.inheritance} aria-label="Inherited category">
        <div>
          <span className={styles.categoryMark} aria-hidden="true" style={{ backgroundColor: category?.color ?? '#798186' }} />
          <p><strong>{categoryLabel}</strong><span>Inherited by every card in this deck</span></p>
        </div>
        <Link to="/flashcards">Edit category on the deck</Link>
      </section>

      {deck.deleted_at ? (
        <section className={styles.removedDeck}>
          <div>
            <h2>This deck is removed.</h2>
            <p>Its cards are retained but cannot be changed or reviewed until the deck is restored.</p>
          </div>
          <button
            className={styles.primary}
            disabled={mutation.isPending}
            onClick={() => mutation.mutate({ kind: 'restore-deck' })}
          >
            {mutation.isPending ? 'Restoring...' : 'Restore deck'}
          </button>
        </section>
      ) : (
        <section className={styles.reviewSetup} aria-labelledby="review-setup-heading">
          {activeReview ? (
            <>
              <div>
                <p>REVIEW / IN PROGRESS</p>
                <h2 id="review-setup-heading">
                  {activeReviewIsThisDeck ? 'Your place is saved.' : 'Another review is already open.'}
                </h2>
                <span>{activeReview.reviewed_card_count} reviewed / {activeReview.remaining_due_card_count} remaining</span>
              </div>
              <Link to={`/flashcards/review/${activeReview.session.id}`}>Resume review</Link>
            </>
          ) : showReviewSetup ? (
            <>
              <div>
                <p>REVIEW / READY</p>
                <h2 id="review-setup-heading">Review {deck.due_card_count} due {deck.due_card_count === 1 ? 'card' : 'cards'}?</h2>
                <span>The queue follows the server's due order. You can leave and resume without losing your place.</span>
              </div>
              <div className={styles.reviewActions}>
                <button className={styles.primary} disabled={startMutation.isPending} onClick={() => startMutation.mutate()}>
                  {startMutation.isPending ? 'Starting...' : 'Start review'}
                </button>
                <button onClick={() => setShowReviewSetup(false)}>Not now</button>
              </div>
            </>
          ) : (
            <>
              <div>
                <p>REVIEW / QUEUE</p>
                <h2 id="review-setup-heading">{deck.due_card_count > 0 ? `${deck.due_card_count} ready for recall.` : 'Nothing is due right now.'}</h2>
                <span>{deck.due_card_count > 0 ? 'Open a focused review when you are ready.' : 'New and scheduled cards will appear here when due.'}</span>
              </div>
              <button
                className={styles.primary}
                disabled={deck.due_card_count === 0}
                onClick={() => setShowReviewSetup(true)}
              >
                Review due cards
              </button>
            </>
          )}
        </section>
      )}

      {(validationError || mutation.isError || startMutation.isError) && (
        <p className={styles.error} role="alert">{validationError || requestErrorMessage}</p>
      )}

      {!deck.deleted_at && !activeReviewIsThisDeck && showCreate && (
        <form className={styles.cardForm} onSubmit={handleCreate} aria-label="Create card">
          <div className={styles.formHeading}>
            <div><p>NEW / CARD</p><h2>Write for recall, not recognition.</h2></div>
            <button type="button" onClick={() => setShowCreate(false)}>Close</button>
          </div>
          <div className={styles.faceGrid}>
            <label>
              Front (Markdown)
              <textarea
                value={front}
                maxLength={20_000}
                onChange={(event) => setFront(event.target.value)}
                autoFocus
                required
              />
            </label>
            <div className={styles.preview} aria-label="Front preview">
              <span>Front preview</span>
              {front.trim() ? <MarkdownContent source={front} /> : <p>Preview appears here.</p>}
            </div>
            <label>
              Back (Markdown)
              <textarea
                value={back}
                maxLength={20_000}
                onChange={(event) => setBack(event.target.value)}
                required
              />
            </label>
            <div className={styles.preview} aria-label="Back preview">
              <span>Back preview</span>
              {back.trim() ? <MarkdownContent source={back} /> : <p>Preview appears here.</p>}
            </div>
          </div>
          <label className={styles.positionField}>
            Position <span>optional, added last when empty</span>
            <input type="number" min="0" step="1" value={position} onChange={(event) => setPosition(event.target.value)} />
          </label>
          <button className={styles.primary} type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Adding card...' : 'Add card'}
          </button>
        </form>
      )}

      <section className={styles.cardsSection} aria-labelledby="cards-heading">
        <div className={styles.toolbar}>
          <div><p>CARDS / {String(cards.length).padStart(2, '0')}</p><h2 id="cards-heading">Card library</h2></div>
          <div className={styles.toolbarActions}>
            <label>
              <input type="checkbox" checked={showRemoved} onChange={(event) => setShowRemoved(event.target.checked)} />
              Include removed
            </label>
            {!deck.deleted_at && (
              <button
                disabled={mutation.isPending || activeReviewIsThisDeck}
                onClick={() => {
                  if (activeReviewIsThisDeck) return;
                  setShowCreate((visible) => !visible);
                  setEditingId(null);
                  setValidationError('');
                  mutation.reset();
                }}
              >
                {showCreate ? 'Close new card' : 'New card'}
              </button>
            )}
          </div>
        </div>

        {activeReviewIsThisDeck && (
          <p className={styles.lockNotice} role="status">
            Card changes are locked while this deck's review is in progress. Resume or finish the review to unlock them.
          </p>
        )}

        {cards.length === 0 ? (
          <StatusBlock
            title={showRemoved ? 'No cards found' : 'This deck has no active cards'}
            detail={deck.deleted_at ? 'Restore the deck before adding cards.' : 'Add a question and answer to begin this deck.'}
          />
        ) : (
          <div className={styles.cardList}>
            {cards.map((card) => {
              const dueNow = Date.parse(card.schedule.due_at) <= Date.now();
              return (
                <article className={`${styles.card} ${card.deleted_at ? styles.removed : ''}`} key={card.id}>
                  {editingId === card.id ? (
                    <div className={styles.cardEditor}>
                      <div className={styles.formHeading}>
                        <div><p>EDIT / CARD {card.position}</p><h3>Source remains unchanged until you save.</h3></div>
                      </div>
                      <div className={styles.faceGrid}>
                        <label>
                          Front (Markdown)
                          <textarea value={editFront} maxLength={20_000} onChange={(event) => setEditFront(event.target.value)} />
                        </label>
                        <div className={styles.preview} aria-label="Edited front preview"><span>Front preview</span><MarkdownContent source={editFront} /></div>
                        <label>
                          Back (Markdown)
                          <textarea value={editBack} maxLength={20_000} onChange={(event) => setEditBack(event.target.value)} />
                        </label>
                        <div className={styles.preview} aria-label="Edited back preview"><span>Back preview</span><MarkdownContent source={editBack} /></div>
                      </div>
                      <label className={styles.positionField}>
                        Position
                        <input type="number" min="0" step="1" value={editPosition} onChange={(event) => setEditPosition(event.target.value)} />
                      </label>
                      <div className={styles.formActions}>
                        <button className={styles.primary} disabled={mutation.isPending || activeReviewIsThisDeck} onClick={() => saveEdit(card)}>Save card</button>
                        <button onClick={() => setEditingId(null)}>Cancel</button>
                      </div>
                    </div>
                  ) : confirmDeleteId === card.id ? (
                    <div className={styles.confirm} aria-live="polite">
                      <div>
                        <h3 id={`remove-card-${card.id}`}>Remove this card?</h3>
                        <p>Past review events remain in history. The card leaves future due queues and can be restored later.</p>
                      </div>
                      <div className={styles.formActions}>
                        <button className={styles.destructive} disabled={mutation.isPending || activeReviewIsThisDeck} onClick={() => runCardAction({ kind: 'delete', id: card.id })}>Remove card</button>
                        <button onClick={() => setConfirmDeleteId(null)}>Keep card</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className={styles.cardMeta}>
                        <span>Position {card.position}</span>
                        <span>{card.deleted_at ? 'Removed' : dueNow ? 'Due now' : `Due ${new Date(card.schedule.due_at).toLocaleDateString()}`}</span>
                        <span>{card.schedule.repetitions} reviews / {card.schedule.interval_days}d interval</span>
                      </div>
                      <div className={styles.cardFaces}>
                        <div><span>Front</span><MarkdownContent source={card.front_markdown} /></div>
                        <div><span>Back</span><MarkdownContent source={card.back_markdown} /></div>
                      </div>
                      <div className={styles.cardActions}>
                        {card.deleted_at ? (
                          <button
                            disabled={mutation.isPending || Boolean(deck.deleted_at) || activeReviewIsThisDeck}
                            title={deck.deleted_at
                              ? 'Restore the deck first'
                              : activeReviewIsThisDeck
                                ? 'Cards are locked while this review is in progress'
                                : undefined}
                            onClick={() => runCardAction({ kind: 'restore', id: card.id })}
                          >
                            Restore card
                          </button>
                        ) : !deck.deleted_at ? (
                          <>
                            <button disabled={activeReviewIsThisDeck} onClick={() => beginEdit(card)}>Edit</button>
                            <button className={styles.removeButton} disabled={activeReviewIsThisDeck} onClick={() => setConfirmDeleteId(card.id)}>Remove</button>
                          </>
                        ) : null}
                      </div>
                    </>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
