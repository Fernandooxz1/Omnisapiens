import type { MessageKey } from '#lib/i18n';
import type { CaseMeta, DifficultyKey, GameAccent } from './types';

/** De menor a mayor: la UI lista y agrupa los niveles siempre en este orden. */
export const DIFFICULTIES: readonly DifficultyKey[] = [
	'very_easy',
	'easy',
	'medium',
	'hard',
	'very_hard',
	'hardcore'
];

/** `Todo` en los chips del catálogo. */
export type DifficultyFilter = DifficultyKey | 'all';

export const DIFFICULTY_LABEL: Record<DifficultyKey, MessageKey> = {
	very_easy: 'games.difficulty.very_easy',
	easy: 'games.difficulty.easy',
	medium: 'games.difficulty.medium',
	hard: 'games.difficulty.hard',
	very_hard: 'games.difficulty.very_hard',
	hardcore: 'games.difficulty.hardcore'
};

/** Familia de color del sello; los tokens `--diff*` los define `app.css`. */
export const DIFFICULTY_TONE: Record<DifficultyKey, GameAccent> = {
	very_easy: 'green',
	easy: 'blue',
	medium: 'yellow',
	hard: 'orange',
	very_hard: 'red',
	hardcore: 'purple'
};

export const DIFFICULTY_RANK: Record<DifficultyKey, number> = {
	very_easy: 0,
	easy: 1,
	medium: 2,
	hard: 3,
	very_hard: 4,
	hardcore: 5
};

export function isDifficultyKey(value: unknown): value is DifficultyKey {
	return DIFFICULTIES.includes(value as DifficultyKey);
}

export function countByDifficulty(cases: CaseMeta[]): Record<DifficultyKey, number> {
	const counts: Record<DifficultyKey, number> = {
		very_easy: 0,
		easy: 0,
		medium: 0,
		hard: 0,
		very_hard: 0,
		hardcore: 0
	};

	for (const entry of cases) counts[entry.difficulty] += 1;

	return counts;
}
