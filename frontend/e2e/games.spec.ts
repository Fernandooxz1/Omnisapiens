import { expect, test, type Page } from '@playwright/test';

const caseLinks = (page: Page) => page.getByRole('link', { name: /^Caso \d+,/ });

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
	await expect(caseLinks(page)).toHaveCount(2);
	await expect(tabs.getByRole('link', { name: 'Juegos' })).toHaveAttribute('aria-current', 'page');
});

test('an unknown game offers the way back to the hub', async ({ page }) => {
	await page.goto('/juegos/sudoku');

	await expect(page.getByRole('heading', { level: 1, name: 'Ese juego no existe' })).toBeVisible();

	await page.getByRole('link', { name: 'Volver a Juegos' }).click();
	await expect(page).toHaveURL(/\/juegos$/);
	await expect(page.getByRole('link', { name: /Murdoku/ })).toBeVisible();
});

test('the catalog shows the fixture envelopes and the chips filter them', async ({ page }) => {
	await page.goto('/juegos/murdoku');

	const five = page.getByRole('link', { name: 'Caso 1, El estudio, Muy fácil, 5×5, Sin abrir' });
	const nine = page.getByRole('link', {
		name: 'Caso 21, La biblioteca, Medio, 9×9, Sin abrir'
	});

	await expect(caseLinks(page)).toHaveCount(2);
	await expect(five).toBeVisible();
	await expect(nine).toBeVisible();

	const chips = page.getByRole('group', { name: 'Dificultad' });
	await expect(chips.getByRole('button', { name: /^Todo/ })).toHaveAttribute('aria-pressed', 'true');
	await expect(chips.getByRole('button', { name: /^Fácil/ })).toBeDisabled();

	await chips.getByRole('button', { name: /^Medio/ }).click();
	await expect(chips.getByRole('button', { name: /^Medio/ })).toHaveAttribute(
		'aria-pressed',
		'true'
	);
	await expect(caseLinks(page)).toHaveCount(1);
	await expect(nine).toBeVisible();
	await expect(five).toHaveCount(0);

	await chips.getByRole('button', { name: /^Todo/ }).click();
	await expect(caseLinks(page)).toHaveCount(2);
});

test('the catalog does not scroll sideways on a phone', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.goto('/juegos/murdoku');

	await expect(caseLinks(page)).toHaveCount(2);

	const overflow = await page.evaluate(
		() => document.documentElement.scrollWidth - document.documentElement.clientWidth
	);
	expect(overflow).toBeLessThanOrEqual(0);
});
