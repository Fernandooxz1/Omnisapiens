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

test('the home reserves the space of the catalog while it loads', async ({ page }) => {
	let release!: () => void;
	const gate = new Promise<void>((resolve) => (release = resolve));

	await page.route(/\/modes$/, async (route) => {
		await gate;
		await route.fulfill({
			status: 200,
			headers: { 'access-control-allow-origin': '*' },
			json: [mode('trivia_arcade', 'Arcade', true)]
		});
	});

	await page.goto('/');
	await expect(page.locator('.mode-skeleton')).toHaveCount(2);

	release();
	await expect(page.getByRole('navigation', { name: 'Modos de juego' })).toBeVisible();
});

test('the home retries the catalog after a failure', async ({ page }) => {
	let calls = 0;

	await page.route(/\/modes$/, (route) => {
		calls += 1;

		if (calls === 1) {
			return route.fulfill({
				status: 500,
				headers: { 'access-control-allow-origin': '*' },
				json: { error: { code: 'SERVER', message: 'boom' } }
			});
		}

		return route.fulfill({
			status: 200,
			headers: { 'access-control-allow-origin': '*' },
			json: [mode('trivia_arcade', 'Arcade', true)]
		});
	});

	await page.goto('/');
	await expect(page.getByText('No se pudieron cargar los modos.')).toBeVisible();

	await page.getByRole('button', { name: 'Reintentar' }).click();

	const nav = page.getByRole('navigation', { name: 'Modos de juego' });
	await expect(nav.getByRole('button', { name: /^Arcade/ })).toBeVisible();
	expect(calls).toBe(2);
});
