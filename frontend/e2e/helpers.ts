import { expect, type Page } from '@playwright/test';

export type Mode = 'arcade' | 'online';

/** El nick es único por usuario: cada corrida usa uno distinto para no chocar con la BD. */
export function uniqueNick(prefix: string): string {
	return `${prefix}${Math.random().toString(36).slice(2, 7)}`.slice(0, 16);
}

/** Entra desde el inicio: el nick crea la sesión de invitado y el modo navega. */
export async function enter(page: Page, nick: string, mode: Mode): Promise<void> {
	await page.goto('/');
	await page.getByLabel('Tu nombre').fill(nick);

	const button =
		mode === 'arcade'
			? page.getByRole('button', { name: /^Arcade/ })
			: page.getByRole('button', { name: /^Jugar 1v1/ });
	await button.click();

	await expect(page).toHaveURL(
		mode === 'arcade' ? /\/play\/trivia_arcade$/ : /\/play\/trivia_versus$/
	);
}

/** Crea una sala y devuelve el código que muestra el lobby. */
export async function createRoom(page: Page, rounds: 3 | 5 | 7 = 3): Promise<string> {
	await page.getByRole('button', { name: `${rounds} rondas` }).click();
	await page.getByRole('button', { name: 'Crear sala' }).click();

	await expect(page).toHaveURL(/\/room\/[A-Z2-9]{6}$/);

	const code = await page.locator('.lobby__code').innerText();
	return code.trim();
}

/** El código completo dispara la entrada solo: no hace falta pulsar `Entrar`. */
export async function joinRoom(page: Page, code: string): Promise<void> {
	await page.goto('/play/trivia_versus');
	await page.getByLabel('Carácter 1 de 6').click();
	await page.keyboard.type(code);

	await expect(page).toHaveURL(new RegExp(`/room/${code}$`));
}

/** Espera la pregunta en curso y elige una opción; el servidor resuelve la ronda. */
export async function answerCurrent(page: Page, index = 0): Promise<void> {
	const tiles = page.locator('.match__tiles button');

	await expect(tiles).toHaveCount(4);
	await expect(tiles.nth(index)).toBeEnabled();
	await tiles.nth(index).click();
}
