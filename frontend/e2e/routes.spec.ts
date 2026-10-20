import { expect, test } from '@playwright/test';

test('the old arcade URL redirects to its mode', async ({ page }) => {
	await page.goto('/arcade');
	await expect(page).toHaveURL(/\/play\/trivia_arcade$/);
});

test('the old play URL redirects to the 1v1 mode', async ({ page }) => {
	await page.goto('/play');
	await expect(page).toHaveURL(/\/play\/trivia_versus$/);
});
