import { expect, test } from '@playwright/test';

/** Un modo tal como lo publica `GET /modes`; solo se usan los campos del menú. */
function mode(code: string, name: string, ranking: boolean) {
	return {
		code,
		name,
		content_kind: 'quiz',
		play_format: 'arcade',
		players: 'solo',
		input: 'choice',
		media: ['none'],
		ranking,
		config_schema: { type: 'object', properties: {}, additionalProperties: false }
	};
}

test('the home lists the modes published by the catalog', async ({ page }) => {
	await page.route(/\/modes$/, (route) =>
		route.fulfill({
			status: 200,
			headers: { 'access-control-allow-origin': '*' },
			json: [mode('trivia_arcade', 'Arcade', true), mode('rosco_solo', 'Rosco', false)]
		})
	);

	await page.goto('/');
	await page.getByLabel('Tu nombre').fill('Tester');

	const nav = page.getByRole('navigation', { name: 'Modos de juego' });
	await expect(nav.getByRole('button', { name: /^Arcade/ })).toBeEnabled();

	// Un modo sin renderer no rompe la home: se muestra deshabilitado.
	await expect(nav.getByRole('button', { name: /Rosco/ })).toBeDisabled();
	await expect(nav.getByText('Próximamente.')).toBeVisible();

	// Lo que el backend no publica no aparece, aunque el registry lo conozca.
	await expect(nav.getByRole('button', { name: /Jugar 1v1/ })).toHaveCount(0);
});

test('the home shows the modes from the real backend', async ({ page }) => {
	await page.goto('/');

	const nav = page.getByRole('navigation', { name: 'Modos de juego' });
	await expect(nav.getByRole('button')).toHaveCount(2);
	await expect(nav.getByRole('button', { name: /^Arcade/ })).toBeVisible();
	await expect(nav.getByRole('button', { name: /^Jugar 1v1/ })).toBeVisible();
	await expect(page.getByRole('link', { name: 'Ranking semanal' })).toBeVisible();
});
