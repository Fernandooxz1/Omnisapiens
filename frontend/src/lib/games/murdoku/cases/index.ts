import type { DifficultyKey } from '../../types.ts';
import { largeCases } from './large.ts';
import { standardCases } from './standard.ts';
import type { MurdokuCase } from '../types.ts';

/** Catálogo publicado: 48 estándar (5×5 a 9×9) y 14 grandes (10×10 a 15×15). */
export const allCases: MurdokuCase[] = [...standardCases, ...largeCases].sort(
	(a, b) => a.number - b.number
);

export function findCase(id: string): MurdokuCase | undefined {
	return allCases.find((entry) => entry.id === id);
}

export function byDifficulty(difficulty: DifficultyKey | 'all' = 'all'): MurdokuCase[] {
	if (difficulty === 'all') return allCases;
	return allCases.filter((entry) => entry.difficulty === difficulty);
}
