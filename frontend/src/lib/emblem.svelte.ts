/** El emblema del avatar propio: un accesorio elegido, no un color. */
export type Emblem = 'brain' | 'bolt' | 'crown' | 'flame' | 'glasses' | 'star';

export const EMBLEM_KEY = 'omni-emblem';

export const EMBLEMS: readonly Emblem[] = ['brain', 'bolt', 'crown', 'flame', 'glasses', 'star'];

export const DEFAULT_EMBLEM: Emblem = 'brain';

export function isEmblem(value: unknown): value is Emblem {
	return EMBLEMS.includes(value as Emblem);
}

function readEmblem(): Emblem {
	if (typeof localStorage === 'undefined') return DEFAULT_EMBLEM;
	try {
		const value = localStorage.getItem(EMBLEM_KEY);
		return isEmblem(value) ? value : DEFAULT_EMBLEM;
	} catch {
		return DEFAULT_EMBLEM;
	}
}

let current = $state<Emblem>(readEmblem());

export function getEmblem(): Emblem {
	return current;
}

export function setEmblem(emblem: Emblem): void {
	current = emblem;
	try {
		localStorage.setItem(EMBLEM_KEY, emblem);
	} catch {
		/* sin persistencia: el emblema igual vale para esta sesión */
	}
}
