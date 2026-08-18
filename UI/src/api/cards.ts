import { apiRequest, toQueryString } from './client';
import type {
  CreateCardRequest,
  Flashcard,
  UpdateCardRequest,
} from './contracts';

export function getCards(deckId: string, includeDeleted = false): Promise<Flashcard[]> {
  return apiRequest<Flashcard[]>(
    `/decks/${encodeURIComponent(deckId)}/cards${toQueryString({ include_deleted: includeDeleted })}`,
  );
}

export function getCard(id: string, includeDeleted = false): Promise<Flashcard> {
  return apiRequest<Flashcard>(
    `/cards/${encodeURIComponent(id)}${toQueryString({ include_deleted: includeDeleted })}`,
  );
}

export function createCard(deckId: string, payload: CreateCardRequest): Promise<Flashcard> {
  return apiRequest<Flashcard>(`/decks/${encodeURIComponent(deckId)}/cards`, {
    method: 'POST',
    body: payload,
  });
}

export function updateCard(id: string, payload: UpdateCardRequest): Promise<Flashcard> {
  return apiRequest<Flashcard>(`/cards/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteCard(id: string): Promise<void> {
  return apiRequest<void>(`/cards/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function restoreCard(id: string): Promise<Flashcard> {
  return apiRequest<Flashcard>(`/cards/${encodeURIComponent(id)}/restore`, { method: 'POST' });
}

export function getDueCards(deckId: string): Promise<Flashcard[]> {
  return apiRequest<Flashcard[]>(`/decks/${encodeURIComponent(deckId)}/due-cards`);
}
