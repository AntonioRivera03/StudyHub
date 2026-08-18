import { expect, test, type Page } from '@playwright/test';

async function completeFlashcardFlow(page: Page, mobile = false) {
  if (mobile) await page.setViewportSize({ width: 320, height: 720 });
  const suffix = `${mobile ? 'Mobile' : 'Desktop'} ${Date.now()}`;
  const deckName = `Recall flow ${suffix}`;
  const front = `**Prompt** ${suffix}`;
  const back = `Answer ${suffix}`;

  await page.goto('/flashcards');
  await expect(page.getByRole('heading', { name: 'Your decks' })).toBeVisible();
  await page.getByRole('button', { name: 'New deck' }).click();
  await page.getByLabel('Deck name').fill(deckName);
  await page.getByLabel(/Description/).fill('Playwright authoring and review flow');
  await page.getByRole('button', { name: 'Create deck' }).click();

  await page.getByRole('link', { name: deckName, exact: true }).click();
  await expect(page.getByRole('heading', { name: deckName })).toBeVisible();
  await page.getByRole('button', { name: 'New card' }).click();
  await page.getByLabel('Front (Markdown)').fill(front);
  await page.getByLabel('Back (Markdown)').fill(back);
  await expect(page.getByLabel('Front preview')).toContainText('Prompt');
  await page.getByRole('button', { name: 'Add card' }).click();

  await expect(page.getByText('Due now', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Review due cards' }).click();
  await page.getByRole('button', { name: 'Start review' }).click();
  await expect(page.getByText('Prompt', { exact: false })).toBeVisible();

  await page.getByRole('link', { name: 'Leave and resume later' }).click();
  await expect(page.getByText('Your place is saved.')).toBeVisible();
  await page.getByRole('link', { name: 'Resume review' }).click();
  await page.getByRole('button', { name: 'Show answer' }).click();
  await expect(page.getByRole('button', { name: /Again/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Hard/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Good/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Easy/ })).toBeVisible();
  await page.keyboard.press('3');

  await expect(page.getByText('QUEUE / CLEAR')).toBeVisible();
  await page.getByRole('button', { name: 'Complete review' }).click();
  await expect(page.getByRole('heading', { name: 'Review complete.' })).toBeVisible();
  await page.getByRole('link', { name: 'Return to deck' }).click();

  await page.getByRole('button', { name: 'Remove' }).click();
  await page.getByRole('button', { name: 'Remove card' }).click();
  await page.getByLabel('Include removed').click();
  await page.getByRole('button', { name: 'Restore card' }).click();

  await page.getByRole('link', { name: 'Back to decks' }).click();
  const deckRow = page.getByRole('article').filter({ hasText: deckName });
  await deckRow.getByRole('button', { name: 'Remove' }).click();
  await deckRow.getByRole('button', { name: 'Remove deck' }).click();
  await page.getByLabel('Include removed').click();
  const removedDeckRow = page.getByRole('article').filter({ hasText: deckName });
  await removedDeckRow.getByRole('button', { name: 'Restore' }).click();

  await page.goto('/');
  const cardsReviewed = page.getByText('Cards reviewed').locator('..');
  await expect(cardsReviewed.locator('strong')).not.toHaveText('0');
  await expect(page.getByText('Reviews', { exact: true })).toBeVisible();
}

test('authors, resumes, keyboard-rates, completes, and restores flashcards', async ({ page }) => {
  await completeFlashcardFlow(page);
});

test('keeps the complete flashcard flow operable at 320px', async ({ page }) => {
  await completeFlashcardFlow(page, true);
});
