import { apiRequest, toQueryString } from './client';
import type {
  CreateDeckRequest,
  FlashcardDeck,
  UpdateDeckRequest,
} from './contracts';

export function getDecks(includeDeleted = false): Promise<FlashcardDeck[]> {
  return apiRequest<FlashcardDeck[]>(`/decks${toQueryString({ include_deleted: includeDeleted })}`);
}

export function getDeck(id: string, includeDeleted = false): Promise<FlashcardDeck> {
  return apiRequest<FlashcardDeck>(
    `/decks/${encodeURIComponent(id)}${toQueryString({ include_deleted: includeDeleted })}`,
  );
}

export function createDeck(payload: CreateDeckRequest): Promise<FlashcardDeck> {
  return apiRequest<FlashcardDeck>('/decks', { method: 'POST', body: payload });
}

export function updateDeck(id: string, payload: UpdateDeckRequest): Promise<FlashcardDeck> {
  return apiRequest<FlashcardDeck>(`/decks/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: payload,
  });
}

export function deleteDeck(id: string): Promise<void> {
  return apiRequest<void>(`/decks/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function restoreDeck(id: string): Promise<FlashcardDeck> {
  return apiRequest<FlashcardDeck>(`/decks/${encodeURIComponent(id)}/restore`, { method: 'POST' });
}
