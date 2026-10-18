import { expect, test } from '@playwright/test';

test('an unknown route renders the error page', async ({ page }) => {
	await page.goto('/no-existe');

	await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toBeVisible();
	await expect(page.getByText('La dirección no existe o cambió de lugar.')).toBeVisible();

	await page.getByRole('button', { name: 'Volver al inicio' }).click();
	await expect(page).toHaveURL(/\/$/);
});

test('an API error surfaces its code and server message', async ({ page }) => {
	await page.route(/\/leaderboard\/arcade\?/, (route) =>
		route.fulfill({
			status: 422,
			contentType: 'application/json',
			headers: { 'access-control-allow-origin': '*' },
			body: JSON.stringify({
				error: { code: 'VALIDATION_ERROR', message: 'El campo limit no es válido.' }
			})
		})
	);

	await page.goto('/ranking');

	const notice = page.getByRole('alert').filter({ hasText: 'VALIDATION_ERROR' });
	await expect(notice).toBeVisible();
	await expect(notice).toContainText('El campo limit no es válido.');

	await notice.getByRole('button', { name: 'Cerrar aviso' }).click();
	await expect(notice).toBeHidden();
});

test('an unreachable API shows the connection notice and recovers', async ({ page }) => {
	await page.route(/\/health$/, (route) => route.abort());
	await page.route(/\/leaderboard\/arcade\?/, (route) => route.abort());

	await page.goto('/ranking');

	const banner = page.getByRole('alert').filter({ hasText: 'Sin conexión con el servidor' });
	await expect(banner).toBeVisible();

	await page.unroute(/\/health$/);
	await page.unroute(/\/leaderboard\/arcade\?/);
	await banner.getByRole('button', { name: 'Reintentar' }).click();

	await expect(banner).toBeHidden();
});
