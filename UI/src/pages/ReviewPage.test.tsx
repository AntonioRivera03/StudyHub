import { fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import type {
  Flashcard,
  FlashcardDeck,
  RateCardRequest,
  ReviewProgress,
} from '../api/contracts';
import { categoryFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { server } from '../test/server';
import { ReviewPage } from './ReviewPage';

const cardFixture: Flashcard = {
  id: 'card-1',
  deck_id: 'deck-1',
  front_markdown: '**Derivative** of x²?',
  back_markdown: '`2x`',
  position: 0,
  schedule: {
    repetitions: 0,
    interval_days: 0,
    ease_factor: 2.5,
    due_at: '2026-08-17T08:00:00.000Z',
    last_reviewed_at: null,
  },
  created_at: '2026-08-17T08:00:00.000Z',
  updated_at: '2026-08-17T08:00:00.000Z',
  deleted_at: null,
};

const deckFixture: FlashcardDeck = {
  id: 'deck-1',
  name: 'Calculus identities',
  description: null,
  category_id: categoryFixture.id,
  active_card_count: 1,
  due_card_count: 1,
  created_at: '2026-08-17T08:00:00.000Z',
  updated_at: '2026-08-17T08:00:00.000Z',
  deleted_at: null,
};

function reviewProgress(overrides: Partial<ReviewProgress> = {}): ReviewProgress {
  return {
    session: {
      id: 'review-1',
      deck_id: deckFixture.id,
      category_id_snapshot: categoryFixture.id,
      status: 'in_progress',
      started_at: '2026-08-17T08:00:00.000Z',
      ended_at: null,
      duration_seconds: 0,
      created_at: '2026-08-17T08:00:00.000Z',
      updated_at: '2026-08-17T08:00:00.000Z',
      deleted_at: null,
    },
    reviewed_card_count: 0,
    remaining_due_card_count: 1,
    next_card: cardFixture,
    ...overrides,
  };
}

function renderReview() {
  return renderWithProviders(
    <Routes><Route path="/flashcards/review/:reviewId" element={<ReviewPage />} /></Routes>,
    '/flashcards/review/review-1',
  );
}

describe('ReviewPage', () => {
  let progress: ReviewProgress;

  beforeEach(() => {
    progress = reviewProgress();
    server.use(
      http.get('*/api/v1/reviews/:reviewId', () => HttpResponse.json(progress)),
      http.get('*/api/v1/decks/:deckId', () => HttpResponse.json(deckFixture)),
      http.get('*/api/v1/categories', () => HttpResponse.json([categoryFixture])),
    );
  });

  it('recovers an interrupted keyboard rating with the same command and completes', async () => {
    const commands: RateCardRequest[] = [];
    let ratingAttempt = 0;
    server.use(
      http.post('*/api/v1/reviews/:reviewId/ratings', async ({ request }) => {
        commands.push(await request.json() as RateCardRequest);
        ratingAttempt += 1;
        if (ratingAttempt === 1) {
          return HttpResponse.json({ error: { code: 'temporary', message: 'Connection interrupted' } }, { status: 503 });
        }
        progress = reviewProgress({
          reviewed_card_count: 1,
          remaining_due_card_count: 0,
          next_card: null,
        });
        return HttpResponse.json({
          event: {
            id: 'event-1',
            command_id: commands[0]?.command_id,
            review_session_id: 'review-1',
            card_id: 'card-1',
            sequence: 1,
            rating: 'good',
            quality: 4,
            reviewed_at: '2026-08-17T08:01:00.000Z',
            previous_schedule: cardFixture.schedule,
            new_schedule: { ...cardFixture.schedule, repetitions: 1, interval_days: 1 },
          },
          progress,
        });
      }),
      http.post('*/api/v1/reviews/:reviewId/complete', () => {
        progress = {
          ...progress,
          session: {
            ...progress.session,
            status: 'completed',
            ended_at: '2026-08-17T08:02:00.000Z',
            duration_seconds: 120,
          },
        };
        return HttpResponse.json(progress);
      }),
    );
    const user = userEvent.setup();
    renderReview();

    expect(await screen.findByText('Derivative')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Again/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Hard/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Good/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Easy/ })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Show answer' }));
    await user.keyboard('3');
    expect(await screen.findByRole('heading', { name: 'Rating confirmation was interrupted.' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Retry same rating' }));

    expect(await screen.findByRole('heading', { name: 'You reviewed 1 card.' })).toBeInTheDocument();
    expect(commands).toHaveLength(2);
    expect(commands[0]).toEqual(commands[1]);
    expect(commands[0]?.rating).toBe('good');

    await user.click(screen.getByRole('button', { name: 'Complete review' }));
    expect(await screen.findByRole('heading', { name: 'Review complete.' })).toBeInTheDocument();
    expect(screen.getByText('2m')).toBeInTheDocument();
  });

  it('resumes saved progress and can explicitly abandon it', async () => {
    progress = reviewProgress({ reviewed_card_count: 1, remaining_due_card_count: 1 });
    server.use(
      http.post('*/api/v1/reviews/:reviewId/abandon', () => {
        progress = {
          ...progress,
          session: {
            ...progress.session,
            status: 'abandoned',
            ended_at: '2026-08-17T08:02:00.000Z',
            duration_seconds: 120,
          },
        };
        return HttpResponse.json(progress);
      }),
    );
    const user = userEvent.setup();
    renderReview();

    await waitFor(() => expect(screen.getByLabelText('Review progress')).toHaveTextContent('1reviewed'));
    await user.click(screen.getByRole('button', { name: 'Abandon review' }));
    expect(screen.getByRole('heading', { name: 'Abandon this review?' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Abandon review' }));
    expect(await screen.findByRole('heading', { name: 'Review stopped.' })).toBeInTheDocument();
  });

  it('ignores modified rating shortcuts', async () => {
    let ratingRequests = 0;
    server.use(
      http.post('*/api/v1/reviews/:reviewId/ratings', () => {
        ratingRequests += 1;
        return HttpResponse.json({}, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderReview();

    await user.click(await screen.findByRole('button', { name: 'Show answer' }));
    await user.keyboard('{Control>}3{/Control}');

    expect(ratingRequests).toBe(0);
    expect(screen.getByRole('button', { name: /Good/ })).toBeEnabled();
  });

  it('keeps the same retry command when reloaded progress is stale', async () => {
    const commands: RateCardRequest[] = [];
    server.use(
      http.post('*/api/v1/reviews/:reviewId/ratings', async ({ request }) => {
        commands.push(await request.json() as RateCardRequest);
        if (commands.length === 1) {
          return HttpResponse.json(
            { error: { code: 'temporary', message: 'Connection interrupted' } },
            { status: 503 },
          );
        }
        const completedProgress = reviewProgress({
          reviewed_card_count: 1,
          remaining_due_card_count: 0,
          next_card: null,
        });
        return HttpResponse.json({
          event: {
            id: 'event-1',
            command_id: commands[0]?.command_id,
            review_session_id: 'review-1',
            card_id: 'card-1',
            sequence: 1,
            rating: 'good',
            quality: 4,
            reviewed_at: '2026-08-17T08:01:00.000Z',
            previous_schedule: cardFixture.schedule,
            new_schedule: { ...cardFixture.schedule, repetitions: 1, interval_days: 1 },
          },
          progress: completedProgress,
        });
      }),
    );
    const user = userEvent.setup();
    renderReview();

    await user.click(await screen.findByRole('button', { name: 'Show answer' }));
    await user.click(screen.getByRole('button', { name: /Good/ }));
    await user.click(await screen.findByRole('button', { name: 'Reload saved progress' }));

    expect(await screen.findByText(/This rating is not saved yet/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Retry same rating' }));
    expect(await screen.findByRole('heading', { name: 'You reviewed 1 card.' })).toBeInTheDocument();
    expect(commands).toHaveLength(2);
    expect(commands[0]).toEqual(commands[1]);
  });

  it('keeps loaded progress when deck metadata or categories fail', async () => {
    server.use(
      http.get('*/api/v1/decks/:deckId', () => HttpResponse.json({}, { status: 500 })),
      http.get('*/api/v1/categories', () => HttpResponse.json({}, { status: 500 })),
    );
    renderReview();

    expect(await screen.findByText('Derivative')).toBeInTheDocument();
    expect(screen.getByText('REVIEW / DECK')).toBeInTheDocument();
    expect(screen.getByText('Category snapshot: Unsorted')).toBeInTheDocument();
  });

  it('exposes rating keyboard shortcuts on the rating buttons', async () => {
    renderReview();
    await screen.findByText('Derivative');

    expect(screen.getByRole('button', { name: /Again/ })).toHaveAttribute('aria-keyshortcuts', '1');
    expect(screen.getByRole('button', { name: /Hard/ })).toHaveAttribute('aria-keyshortcuts', '2');
    expect(screen.getByRole('button', { name: /Good/ })).toHaveAttribute('aria-keyshortcuts', '3');
    expect(screen.getByRole('button', { name: /Easy/ })).toHaveAttribute('aria-keyshortcuts', '4');
  });

  it('ignores rating shortcuts when focus is on a button or link', async () => {
    let ratingRequests = 0;
    server.use(
      http.post('*/api/v1/reviews/:reviewId/ratings', () => {
        ratingRequests += 1;
        return HttpResponse.json({}, { status: 500 });
      }),
    );
    const user = userEvent.setup();
    renderReview();

    const reveal = await screen.findByRole('button', { name: 'Show answer' });
    await user.click(reveal);
    fireEvent.keyDown(reveal, { key: '3' });
    expect(ratingRequests).toBe(0);
    expect(screen.getByRole('button', { name: /Good/ })).toBeEnabled();

    const resumeLink = screen.getByRole('link', { name: 'Leave and resume later' });
    fireEvent.keyDown(resumeLink, { key: '3' });
    expect(ratingRequests).toBe(0);
  });
});
