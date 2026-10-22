import { expect, test } from '@playwright/test';

test('the tab bar leads from the home to the games hub and the catalog', async ({ page }) => {
	await page.goto('/');

	const tabs = page.getByRole('navigation', { name: 'Navegación principal' });
	await expect(tabs.getByRole('link', { name: 'Inicio' })).toHaveAttribute('aria-current', 'page');

	await tabs.getByRole('link', { name: 'Juegos' }).click();
	await expect(page).toHaveURL(/\/juegos$/);
	await expect(page.getByRole('heading', { level: 1, name: 'Juegos' })).toBeVisible();

	const murdoku = page.getByRole('link', { name: /Murdoku/ });
	await expect(murdoku).toBeVisible();
	await expect(murdoku).toContainText('62 casos');

	await tabs.getByRole('link', { name: 'Juegos' }).click();
	await expect(page).toHaveURL(/\/juegos$/);

	await murdoku.click();
	await expect(page).toHaveURL(/\/juegos\/murdoku$/);
	await expect(page.getByRole('heading', { level: 1, name: 'Murdoku' })).toBeVisible();
	await expect(page.getByText('Catálogo en preparación')).toBeVisible();
	await expect(tabs.getByRole('link', { name: 'Juegos' })).toHaveAttribute('aria-current', 'page');
});

test('an unknown game offers the way back to the hub', async ({ page }) => {
	await page.goto('/juegos/sudoku');

	await expect(page.getByRole('heading', { level: 1, name: 'Ese juego no existe' })).toBeVisible();

	await page.getByRole('link', { name: 'Volver a Juegos' }).click();
	await expect(page).toHaveURL(/\/juegos$/);
	await expect(page.getByRole('link', { name: /Murdoku/ })).toBeVisible();
});
