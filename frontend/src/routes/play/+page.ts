import { redirect } from '@sveltejs/kit';

/** La URL vieja del 1v1: la pantalla ahora es la del modo. */
export function load() {
	redirect(307, '/play/trivia_versus');
}
