import type { MessageKey } from '#lib/i18n';

/** Las seis categorías del juego; el color lo pone el badge de la pregunta. */
export type Category = 'science' | 'geography' | 'history' | 'sports' | 'entertainment' | 'art';

export const CATEGORIES: readonly Category[] = [
	'science',
	'geography',
	'history',
	'sports',
	'entertainment',
	'art'
];

export function isCategory(value: unknown): value is Category {
	return CATEGORIES.includes(value as Category);
}

/** Clave de i18n del nombre de la categoría (`cat.science`…). */
export function categoryKey(category: Category): MessageKey {
	return `cat.${category}`;
}
