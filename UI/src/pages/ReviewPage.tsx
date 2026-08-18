import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getCategories } from '../api/categories';
import { ApiError } from '../api/client';
import type { RateCardRequest, ReviewRating } from '../api/contracts';
import { getDeck } from '../api/decks';
import { queryKeys } from '../api/queryKeys';
import {
  abandonReview,
  completeReview,
  getReview,
  rateReviewCard,
} from '../api/reviews';
import { MarkdownContent } from '../components/MarkdownContent';
import { StatusBlock } from '../components/StatusBlock';
import { formatDuration } from '../lib/time';
import styles from './ReviewPage.module.css';

const ratings: Array<{
  id: ReviewRating;
  label: string;
  key: string;
  hint: string;
}> = [
  { id: 'again', label: 'Again', key: '1', hint: 'Reset and relearn' },
  { id: 'hard', label: 'Hard', key: '2', hint: 'Shorter interval' },
  { id: 'good', label: 'Good', key: '3', hint: 'Expected interval' },
  { id: 'easy', label: 'Easy', key: '4', hint: 'Longer interval' },
];

type TerminalAction = 'complete' | 'abandon';

export function ReviewPage() {
  const { reviewId = '' } = useParams();
  const queryClient = useQueryClient();
  const [answerVisible, setAnswerVisible] = useState(false);
  const [pendingRatingCommand, setPendingRatingCommand] = useState<RateCardRequest | null>(null);
  const [confirmAbandon, setConfirmAbandon] = useState(false);
  const [recoveryError, setRecoveryError] = useState('');

  const reviewQuery = useQuery({
    queryKey: queryKeys.review(reviewId),
    queryFn: () => getReview(reviewId),
    enabled: Boolean(reviewId),
  });
  const deckId = reviewQuery.data?.session.deck_id ?? '';
  const deckQuery = useQuery({
    queryKey: queryKeys.deck(deckId, true),
    queryFn: () => getDeck(deckId, true),
    enabled: Boolean(deckId),
  });
  const categoriesQuery = useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => getCategories(true),
  });

  const ratingMutation = useMutation({
    mutationFn: (command: RateCardRequest) => rateReviewCard(reviewId, command),
    onSuccess: async (result) => {
      queryClient.setQueryData(queryKeys.review(reviewId), result.progress);
      queryClient.setQueryData(queryKeys.activeReview, result.progress);
      setPendingRatingCommand(null);
      setAnswerVisible(false);
      setRecoveryError('');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['decks'] }),
        queryClient.invalidateQueries({ queryKey: ['cards'] }),
      ]);
    },
  });

  const terminalMutation = useMutation({
    mutationFn: (action: TerminalAction) => (
      action === 'complete' ? completeReview(reviewId) : abandonReview(reviewId)
    ),
    onSuccess: async (progress) => {
      queryClient.setQueryData(queryKeys.review(reviewId), progress);
      setConfirmAbandon(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.activeReview }),
        queryClient.invalidateQueries({ queryKey: ['decks'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]);
    },
  });

  const nextCardId = reviewQuery.data?.next_card?.id;
  useEffect(() => {
    setAnswerVisible(false);
  }, [nextCardId]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target;
      if (
        target instanceof HTMLElement
        && (target.isContentEditable || ['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON', 'A'].includes(target.tagName))
      ) return;
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (!answerVisible || pendingRatingCommand || ratingMutation.isPending) return;
      const rating = ratings.find((item) => item.key === event.key);
      const card = reviewQuery.data?.next_card;
      if (!rating || !card) return;
      event.preventDefault();
      const command: RateCardRequest = {
        command_id: crypto.randomUUID(),
        card_id: card.id,
        rating: rating.id,
      };
      setPendingRatingCommand(command);
      ratingMutation.mutate(command);
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [answerVisible, pendingRatingCommand, ratingMutation, reviewQuery.data?.next_card]);

  function submitRating(rating: ReviewRating) {
    const card = reviewQuery.data?.next_card;
    if (!card || !answerVisible || pendingRatingCommand || ratingMutation.isPending) return;
    const command: RateCardRequest = {
      command_id: crypto.randomUUID(),
      card_id: card.id,
      rating,
    };
    setPendingRatingCommand(command);
    ratingMutation.mutate(command);
  }

  async function reloadProgress() {
    setRecoveryError('');
    const result = await reviewQuery.refetch();
    if (result.isError || !result.data) {
      setRecoveryError('Saved progress could not be checked. Retry the same rating instead.');
      return;
    }
    if (result.data.next_card?.id === pendingRatingCommand?.card_id) {
      setRecoveryError('This rating is not saved yet. Retry the same rating to keep its command ID.');
      return;
    }
    setPendingRatingCommand(null);
    setAnswerVisible(false);
    ratingMutation.reset();
  }

  const isLoading = reviewQuery.isLoading;
  const hasLoadError = reviewQuery.isError;

  if (isLoading) {
    return <div className={styles.page}><StatusBlock title="Recovering your review..." /></div>;
  }

  if (hasLoadError || !reviewQuery.data) {
    return (
      <div className={styles.page}>
        <Link className={styles.backLink} to="/flashcards">Back to decks</Link>
        <StatusBlock
          tone="error"
          title="Review progress could not be loaded"
          detail="Your saved position remains on the server. Try recovering it again."
          action={<button className={styles.retry} onClick={() => void reviewQuery.refetch()}>Try again</button>}
        />
      </div>
    );
  }

  const progress = reviewQuery.data;
  const session = progress.session;
  const card = progress.next_card;
  const deck = deckQuery.data;
  const category = (categoriesQuery.data ?? []).find((item) => item.id === session.category_id_snapshot);
  const categorySnapshot = !category
    ? 'Unsorted'
    : category.deleted_at
      ? `${category.name} (removed)`
      : category.name;
  const mutationError = ratingMutation.error ?? terminalMutation.error;
  const mutationErrorMessage = mutationError instanceof ApiError
    ? mutationError.message
    : 'The request did not finish. Your saved progress has not been replaced.';
  const isInProgress = session.status === 'in_progress';

  if (!isInProgress) {
    return (
      <div className={styles.page}>
        <Link className={styles.backLink} to={`/flashcards/decks/${session.deck_id}`}>Back to deck</Link>
        <main className={styles.summary}>
          <p>REVIEW / {session.status === 'completed' ? 'COMPLETE' : 'ABANDONED'}</p>
          <h1>{session.status === 'completed' ? 'Review complete.' : 'Review stopped.'}</h1>
          <span>
            {session.status === 'completed'
              ? 'The cards you rated have new due dates. This completed review now contributes to today.'
              : 'Rated cards kept their schedule changes, but this review does not count toward today.'}
          </span>
          <section className={styles.summaryStats} aria-label="Review summary">
            <div><strong>{progress.reviewed_card_count}</strong><span>cards reviewed</span></div>
            <div><strong>{formatDuration(session.duration_seconds)}</strong><span>elapsed time</span></div>
            <div><strong>{categorySnapshot}</strong><span>category at start</span></div>
          </section>
          <div className={styles.summaryActions}>
            <Link className={styles.primaryLink} to={`/flashcards/decks/${session.deck_id}`}>Return to deck</Link>
            <Link to="/">View today</Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.reviewHeader}>
        <div>
          <Link className={styles.backLink} to={`/flashcards/decks/${session.deck_id}`}>Leave and resume later</Link>
          <p>REVIEW / {deck?.name ?? 'DECK'}</p>
          <h1>{card ? 'Recall before revealing.' : 'The queue is clear.'}</h1>
        </div>
        <div className={styles.progress} aria-label="Review progress">
          <div><strong>{progress.reviewed_card_count}</strong><span>reviewed</span></div>
          <div><strong>{progress.remaining_due_card_count}</strong><span>remaining</span></div>
        </div>
      </header>

      <div className={styles.contextLine}>
        <span>Category snapshot: {categorySnapshot}</span>
        <span>Started {new Date(session.started_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</span>
      </div>

      {card ? (
        <main className={styles.reviewStage}>
          <article className={styles.reviewCard} aria-live="polite">
            <section className={styles.face} aria-labelledby="front-label">
              <p id="front-label">Front</p>
              <MarkdownContent source={card.front_markdown} className={styles.cardMarkdown} />
            </section>

            {answerVisible ? (
              <section className={`${styles.face} ${styles.answer}`} aria-labelledby="back-label">
                <p id="back-label">Back</p>
                <MarkdownContent source={card.back_markdown} className={styles.cardMarkdown} />
              </section>
            ) : (
              <button className={styles.reveal} onClick={(event) => {
                setAnswerVisible(true);
                event.currentTarget.blur();
              }}>Show answer</button>
            )}
          </article>

          <section className={styles.ratingArea} aria-label="Rate your recall">
            <div className={styles.ratingHeading}>
              <p>How well did you recall it?</p>
              <span>Keyboard: 1 Again, 2 Hard, 3 Good, 4 Easy</span>
            </div>
            <div className={styles.ratings}>
              {ratings.map((rating) => (
                <button
                  key={rating.id}
                  disabled={!answerVisible || ratingMutation.isPending || Boolean(pendingRatingCommand)}
                  onClick={() => submitRating(rating.id)}
                  aria-keyshortcuts={rating.key}
                >
                  <kbd>{rating.key}</kbd>
                  <strong>{rating.label}</strong>
                  <span>{rating.hint}</span>
                </button>
              ))}
            </div>
            {!answerVisible && <p className={styles.ratingNote}>Reveal the answer before rating your recall.</p>}
          </section>
        </main>
      ) : (
        <main className={styles.queueClear}>
          <p>QUEUE / CLEAR</p>
          <h2>You reviewed {progress.reviewed_card_count} {progress.reviewed_card_count === 1 ? 'card' : 'cards'}.</h2>
          <span>Completion is explicit. Finish now to save elapsed time and add this review to today.</span>
          <button className={styles.primary} disabled={terminalMutation.isPending} onClick={() => terminalMutation.mutate('complete')}>
            {terminalMutation.isPending ? 'Completing...' : 'Complete review'}
          </button>
        </main>
      )}

      {ratingMutation.isError && pendingRatingCommand && (
        <section className={styles.recovery} role="alert">
          <div>
            <h2>Rating confirmation was interrupted.</h2>
            <p>{mutationErrorMessage} Retry sends the same command ID, so a server-side success cannot schedule this card twice.</p>
          </div>
          <div>
            <button
              className={styles.primary}
              disabled={ratingMutation.isPending}
              onClick={() => ratingMutation.mutate(pendingRatingCommand)}
            >
              Retry same rating
            </button>
            <button disabled={reviewQuery.isFetching} onClick={() => void reloadProgress()}>
              {reviewQuery.isFetching ? 'Checking...' : 'Reload saved progress'}
            </button>
          </div>
        </section>
      )}

      {(recoveryError || (terminalMutation.isError && !ratingMutation.isError)) && (
        <p className={styles.error} role="alert">{recoveryError || mutationErrorMessage}</p>
      )}

      {isInProgress && !confirmAbandon ? (
        <footer className={styles.reviewFooter}>
          <p>Leaving preserves your exact position. Abandoning is terminal and does not count toward today.</p>
          <button onClick={() => setConfirmAbandon(true)}>Abandon review</button>
        </footer>
      ) : isInProgress ? (
        <footer className={styles.abandonConfirm} aria-live="polite">
          <div>
            <h2 id="abandon-heading">Abandon this review?</h2>
            <p>Existing ratings remain applied, but this review will not contribute duration or cards to today.</p>
          </div>
          <div>
            <button className={styles.destructive} disabled={terminalMutation.isPending} onClick={() => terminalMutation.mutate('abandon')}>
              {terminalMutation.isPending ? 'Abandoning...' : 'Abandon review'}
            </button>
            <button onClick={() => setConfirmAbandon(false)}>Keep reviewing</button>
          </div>
        </footer>
      ) : null}
    </div>
  );
}
