import { apiRequest, toQueryString } from './client';
import type {
  Flashcard,
  RateCardRequest,
  ReviewProgress,
  ReviewRatingResult,
  ReviewSession,
  StartReviewRequest,
} from './contracts';

export function getReviews(includeDeleted = false): Promise<ReviewSession[]> {
  return apiRequest<ReviewSession[]>(
    `/reviews${toQueryString({ include_deleted: includeDeleted })}`,
  );
}

export function startReview(payload: StartReviewRequest): Promise<ReviewProgress> {
  return apiRequest<ReviewProgress>('/reviews', { method: 'POST', body: payload });
}

export function getActiveReview(): Promise<ReviewProgress | null> {
  return apiRequest<ReviewProgress | null>('/reviews/active');
}

export function getReview(id: string, includeDeleted = false): Promise<ReviewProgress> {
  return apiRequest<ReviewProgress>(
    `/reviews/${encodeURIComponent(id)}${toQueryString({ include_deleted: includeDeleted })}`,
  );
}

export function getNextReviewCard(id: string): Promise<Flashcard | null> {
  return apiRequest<Flashcard | null>(`/reviews/${encodeURIComponent(id)}/next`);
}

export function rateReviewCard(id: string, payload: RateCardRequest): Promise<ReviewRatingResult> {
  return apiRequest<ReviewRatingResult>(`/reviews/${encodeURIComponent(id)}/ratings`, {
    method: 'POST',
    body: payload,
  });
}

export function completeReview(id: string): Promise<ReviewProgress> {
  return apiRequest<ReviewProgress>(`/reviews/${encodeURIComponent(id)}/complete`, { method: 'POST' });
}

export function abandonReview(id: string): Promise<ReviewProgress> {
  return apiRequest<ReviewProgress>(`/reviews/${encodeURIComponent(id)}/abandon`, { method: 'POST' });
}

export function deleteReview(id: string): Promise<void> {
  return apiRequest<void>(`/reviews/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function restoreReview(id: string): Promise<ReviewProgress> {
  return apiRequest<ReviewProgress>(`/reviews/${encodeURIComponent(id)}/restore`, { method: 'POST' });
}
