import type { MessageKey } from '#lib/i18n';

/** Las seis categorías del juego; el color lo pone la piel. */
export type Category = 'science' | 'geography' | 'history' | 'sports' | 'entertainment' | 'art';

export const CATEGORIES: readonly Category[] = [
	'science',
	'geography',
	'history',
	'sports',
	'entertainment',
	'art'
];

/** Clave de i18n del nombre de la categoría (`cat.science`…). */
export function categoryKey(category: Category): MessageKey {
	return `cat.${category}`;
}
