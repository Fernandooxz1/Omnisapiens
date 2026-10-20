import { redirect } from '@sveltejs/kit';

/** La URL vieja del arcade: la pantalla ahora es la del modo. */
export function load() {
	redirect(307, '/play/trivia_arcade');
}
