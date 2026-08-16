import { apiRequest, toQueryString } from './client';
import type { Category, CreateCategoryRequest, UpdateCategoryRequest } from './contracts';

export function getCategories(includeDeleted = true): Promise<Category[]> {
  return apiRequest<Category[]>(`/categories${toQueryString({ include_deleted: includeDeleted })}`);
}

export function createCategory(payload: CreateCategoryRequest): Promise<Category> {
  return apiRequest<Category>('/categories', { method: 'POST', body: payload });
}

export function updateCategory(id: string, payload: UpdateCategoryRequest): Promise<Category> {
  return apiRequest<Category>(`/categories/${id}`, { method: 'PATCH', body: payload });
}

export function deleteCategory(id: string): Promise<void> {
  return apiRequest<void>(`/categories/${id}`, { method: 'DELETE' });
}

export function restoreCategory(id: string): Promise<Category> {
  return apiRequest<Category>(`/categories/${id}/restore`, { method: 'POST' });
}
