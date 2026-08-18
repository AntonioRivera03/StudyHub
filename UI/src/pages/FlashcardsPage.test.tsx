import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';
import type { CreateDeckRequest, FlashcardDeck, UpdateDeckRequest } from '../api/contracts';
import { categoryFixture } from '../test/fixtures';
import { renderWithProviders } from '../test/render';
import { server } from '../test/server';
import { FlashcardsPage } from './FlashcardsPage';

const deckFixture: FlashcardDeck = {
  id: 'deck-1',
  name: 'Calculus identities',
  description: 'Core derivatives',
  category_id: categoryFixture.id,
  active_card_count: 3,
  due_card_count: 2,
  created_at: '2026-08-17T08:00:00.000Z',
  updated_at: '2026-08-17T08:00:00.000Z',
  deleted_at: null,
};

describe('FlashcardsPage', () => {
  let decks: FlashcardDeck[];
  let createdPayload: CreateDeckRequest | null;
  let updatedPayload: UpdateDeckRequest | null;

  beforeEach(() => {
    decks = [{ ...deckFixture }];
    createdPayload = null;
    updatedPayload = null;
    server.use(
      http.get('*/api/v1/decks', ({ request }) => {
        const includeDeleted = new URL(request.url).searchParams.get('include_deleted') === 'true';
        return HttpResponse.json(decks.filter((deck) => includeDeleted || !deck.deleted_at));
      }),
      http.post('*/api/v1/decks', async ({ request }) => {
        createdPayload = await request.json() as CreateDeckRequest;
        const deck: FlashcardDeck = {
          ...deckFixture,
          id: 'deck-2',
          name: createdPayload.name,
          description: createdPayload.description ?? null,
          category_id: createdPayload.category_id ?? null,
          active_card_count: 0,
          due_card_count: 0,
        };
        decks.push(deck);
        return HttpResponse.json(deck, { status: 201 });
      }),
      http.patch('*/api/v1/decks/:deckId', async ({ params, request }) => {
        updatedPayload = await request.json() as UpdateDeckRequest;
        const index = decks.findIndex((deck) => deck.id === params.deckId);
        const current = decks[index];
        if (!current) return HttpResponse.json({}, { status: 404 });
        const updated = { ...current, ...updatedPayload } as FlashcardDeck;
        decks[index] = updated;
        return HttpResponse.json(updated);
      }),
      http.delete('*/api/v1/decks/:deckId', ({ params }) => {
        decks = decks.map((deck) => deck.id === params.deckId
          ? { ...deck, deleted_at: '2026-08-17T09:00:00.000Z', due_card_count: 0 }
          : deck);
        return new HttpResponse(null, { status: 204 });
      }),
      http.post('*/api/v1/decks/:deckId/restore', ({ params }) => {
        decks = decks.map((deck) => deck.id === params.deckId
          ? { ...deck, deleted_at: null, due_card_count: 2 }
          : deck);
        return HttpResponse.json(decks.find((deck) => deck.id === params.deckId));
      }),
      http.get('*/api/v1/categories', () => HttpResponse.json([categoryFixture])),
      http.get('*/api/v1/reviews/active', () => HttpResponse.json(null)),
    );
  });

  it('browses due decks and creates one with an inherited category', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FlashcardsPage />, '/flashcards');

    expect(await screen.findByRole('heading', { name: 'Calculus identities' })).toBeInTheDocument();
    expect(screen.getByText('2 due', { exact: true })).toBeInTheDocument();
    expect(screen.getByText('Coursework')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'New deck' }));
    await user.type(screen.getByLabelText('Deck name'), 'Organic chemistry');
    await user.type(screen.getByLabelText(/Description/), 'Reaction recall');
    await user.selectOptions(screen.getByLabelText('Category'), categoryFixture.id);
    await user.click(screen.getByRole('button', { name: 'Create deck' }));

    expect(await screen.findByRole('heading', { name: 'Organic chemistry' })).toBeInTheDocument();
    expect(createdPayload).toEqual({
      name: 'Organic chemistry',
      description: 'Reaction recall',
      category_id: categoryFixture.id,
    });
  });

  it('edits, removes, and restores a deck', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FlashcardsPage />, '/flashcards');

    await screen.findByRole('heading', { name: 'Calculus identities' });
    await user.click(screen.getByRole('button', { name: 'Edit' }));
    await user.clear(screen.getByLabelText('Deck name'));
    await user.type(screen.getByLabelText('Deck name'), 'Calculus essentials');
    await user.click(screen.getByRole('button', { name: 'Save deck' }));

    expect(await screen.findByRole('heading', { name: 'Calculus essentials' })).toBeInTheDocument();
    expect(updatedPayload).toMatchObject({ name: 'Calculus essentials' });

    await user.click(screen.getByRole('button', { name: /^Remove$/ }));
    expect(screen.getByRole('heading', { name: 'Remove Calculus essentials?' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Remove deck' }));
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Calculus essentials' })).not.toBeInTheDocument());

    await user.click(screen.getByLabelText('Include removed'));
    expect(await screen.findByText('Removed', { exact: true })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Restore' }));
    expect(await screen.findByRole('button', { name: /^Remove$/ })).toBeInTheDocument();
  });

  it('keeps the deck library usable when categories or the active review fail', async () => {
    server.use(
      http.get('*/api/v1/categories', () => HttpResponse.json({}, { status: 500 })),
      http.get('*/api/v1/reviews/active', () => HttpResponse.json({}, { status: 500 })),
    );
    renderWithProviders(<FlashcardsPage />, '/flashcards');

    expect(await screen.findByRole('heading', { name: 'Calculus identities' })).toBeInTheDocument();
    expect(screen.getByText('Unsorted')).toBeInTheDocument();
  });

  it('offers resume and prevents removing the deck under active review', async () => {
    server.use(
      http.get('*/api/v1/reviews/active', () => HttpResponse.json({
        session: {
          id: 'review-1',
          deck_id: deckFixture.id,
          category_id_snapshot: deckFixture.category_id,
          status: 'in_progress',
          started_at: '2026-08-17T08:30:00.000Z',
          ended_at: null,
          duration_seconds: 0,
          created_at: '2026-08-17T08:30:00.000Z',
          updated_at: '2026-08-17T08:30:00.000Z',
          deleted_at: null,
        },
        reviewed_card_count: 1,
        remaining_due_card_count: 1,
        next_card: null,
      })),
    );
    renderWithProviders(<FlashcardsPage />, '/flashcards');

    expect(await screen.findByRole('link', { name: 'Resume review' })).toHaveAttribute(
      'href',
      '/flashcards/review/review-1',
    );
    expect(screen.getByRole('button', { name: 'Remove' })).toBeDisabled();
  });
});
