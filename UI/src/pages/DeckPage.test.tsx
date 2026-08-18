import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import type {
  CreateCardRequest,
  Flashcard,
  FlashcardDeck,
  ReviewProgress,
  UpdateCardRequest,
} from '../api/contracts';
import { categoryFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { server } from '../test/server';
import { DeckPage } from './DeckPage';

const deckFixture: FlashcardDeck = {
  id: 'deck-1',
  name: 'Calculus identities',
  description: 'Core derivatives',
  category_id: categoryFixture.id,
  active_card_count: 1,
  due_card_count: 1,
  created_at: '2026-08-17T08:00:00.000Z',
  updated_at: '2026-08-17T08:00:00.000Z',
  deleted_at: null,
};

const cardFixture: Flashcard = {
  id: 'card-1',
  deck_id: deckFixture.id,
  front_markdown: '**Derivative** of x²?',
  back_markdown: '2x',
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

function renderDeck() {
  return renderWithProviders(
    <Routes><Route path="/flashcards/decks/:deckId" element={<DeckPage />} /></Routes>,
    '/flashcards/decks/deck-1',
  );
}

function activeReviewFixture(): ReviewProgress {
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
  };
}

describe('DeckPage', () => {
  let cards: Flashcard[];
  let deck: FlashcardDeck;
  let createdPayload: CreateCardRequest | null;
  let updatedPayload: UpdateCardRequest | null;

  beforeEach(() => {
    cards = [];
    deck = { ...deckFixture, active_card_count: 0, due_card_count: 0 };
    createdPayload = null;
    updatedPayload = null;
    server.use(
      http.get('*/api/v1/decks/:deckId', () => HttpResponse.json(deck)),
      http.get('*/api/v1/decks/:deckId/cards', ({ request }) => {
        const includeDeleted = new URL(request.url).searchParams.get('include_deleted') === 'true';
        return HttpResponse.json(cards.filter((card) => includeDeleted || !card.deleted_at));
      }),
      http.post('*/api/v1/decks/:deckId/cards', async ({ request }) => {
        createdPayload = await request.json() as CreateCardRequest;
        const card: Flashcard = {
          ...cardFixture,
          front_markdown: createdPayload.front_markdown,
          back_markdown: createdPayload.back_markdown,
          position: createdPayload.position ?? 0,
        };
        cards.push(card);
        deck = { ...deck, active_card_count: 1, due_card_count: 1 };
        return HttpResponse.json(card, { status: 201 });
      }),
      http.patch('*/api/v1/cards/:cardId', async ({ request }) => {
        updatedPayload = await request.json() as UpdateCardRequest;
        const current = cards[0];
        if (!current) return HttpResponse.json({}, { status: 404 });
        const updated = { ...current, ...updatedPayload } as Flashcard;
        cards[0] = updated;
        return HttpResponse.json(updated);
      }),
      http.delete('*/api/v1/cards/:cardId', () => {
        cards = cards.map((card) => ({ ...card, deleted_at: '2026-08-17T09:00:00.000Z' }));
        deck = { ...deck, active_card_count: 0, due_card_count: 0 };
        return new HttpResponse(null, { status: 204 });
      }),
      http.post('*/api/v1/cards/:cardId/restore', () => {
        cards = cards.map((card) => ({ ...card, deleted_at: null }));
        deck = { ...deck, active_card_count: 1, due_card_count: 1 };
        return HttpResponse.json(cards[0]);
      }),
      http.get('*/api/v1/categories', () => HttpResponse.json([categoryFixture])),
      http.get('*/api/v1/reviews/active', () => HttpResponse.json(null)),
    );
  });

  it('preserves Markdown source while rendering a sanitized preview', async () => {
    const user = userEvent.setup();
    const { container } = renderDeck();
    const frontSource = '  **Question** <img src=x onerror=alert(1)>  ';
    const backSource = '  `Answer`  ';

    await screen.findByRole('heading', { name: 'Calculus identities' });
    expect(screen.getByText('Inherited by every card in this deck')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'New card' }));
    await user.type(screen.getByLabelText('Front (Markdown)'), frontSource);
    await user.type(screen.getByLabelText('Back (Markdown)'), backSource);

    expect(container.querySelector('img')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Add card' }));

    expect(await screen.findByText('Question', { exact: false })).toBeInTheDocument();
    expect(createdPayload).toEqual({ front_markdown: frontSource, back_markdown: backSource });
  });

  it('edits, removes, and restores a card', async () => {
    cards = [{ ...cardFixture }];
    deck = { ...deckFixture };
    const user = userEvent.setup();
    renderDeck();

    await screen.findByText('Derivative');
    await user.click(screen.getByRole('button', { name: 'Edit' }));
    await user.clear(screen.getByLabelText('Front (Markdown)'));
    await user.type(screen.getByLabelText('Front (Markdown)'), '  Updated **front**  ');
    await user.click(screen.getByRole('button', { name: 'Save card' }));

    await waitFor(() => expect(updatedPayload).toMatchObject({ front_markdown: '  Updated **front**  ' }));
    expect(await screen.findByText('Updated')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Remove' }));
    await user.click(screen.getByRole('button', { name: 'Remove card' }));
    expect(await screen.findByText('This deck has no active cards')).toBeInTheDocument();
    await user.click(screen.getByLabelText('Include removed'));
    expect(await screen.findByText('Removed', { exact: true })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Restore card' }));
    expect(await screen.findByRole('button', { name: 'Edit' })).toBeInTheDocument();
  });

  it('omits position when the edit position is cleared', async () => {
    cards = [{ ...cardFixture }];
    deck = { ...deckFixture };
    const user = userEvent.setup();
    renderDeck();

    await screen.findByText('Derivative');
    await user.click(screen.getByRole('button', { name: 'Edit' }));
    await user.clear(screen.getByLabelText('Position'));
    await user.click(screen.getByRole('button', { name: 'Save card' }));

    await waitFor(() => expect(updatedPayload).not.toBeNull());
    expect(updatedPayload).toEqual({
      front_markdown: '**Derivative** of x²?',
      back_markdown: '2x',
    });
  });

  it('locks card authoring while this deck has an active review and keeps resume available', async () => {
    cards = [{ ...cardFixture }];
    deck = { ...deckFixture };
    server.use(
      http.get('*/api/v1/reviews/active', () => HttpResponse.json(activeReviewFixture())),
    );
    const user = userEvent.setup();
    renderDeck();

    await screen.findByRole('heading', { name: 'Calculus identities' });
    expect(screen.getByRole('link', { name: 'Resume review' })).toBeInTheDocument();
    expect(screen.getByText(/Card changes are locked while this deck's review is in progress/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'New card' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Edit' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Remove' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'New card' }));
    expect(screen.queryByLabelText('Front (Markdown)')).not.toBeInTheDocument();
  });

  it('still opens the deck when categories or the active review fail', async () => {
    cards = [{ ...cardFixture }];
    deck = { ...deckFixture };
    server.use(
      http.get('*/api/v1/categories', () => HttpResponse.json({}, { status: 500 })),
      http.get('*/api/v1/reviews/active', () => HttpResponse.json({}, { status: 500 })),
    );
    renderDeck();

    expect(await screen.findByRole('heading', { name: 'Calculus identities' })).toBeInTheDocument();
    expect(screen.getByText('Unsorted')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit' })).toBeEnabled();
  });
});
