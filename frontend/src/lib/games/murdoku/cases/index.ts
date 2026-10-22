import type { DifficultyKey } from '../../types.ts';
import { standardCases } from './standard.ts';
import type { MurdokuCase } from '../types.ts';

/** Por ahora el catálogo publicado son los 48 casos estándar (5×5 a 9×9). */
export const allCases: MurdokuCase[] = [...standardCases].sort((a, b) => a.number - b.number);

export function findCase(id: string): MurdokuCase | undefined {
	return allCases.find((entry) => entry.id === id);
}

export function byDifficulty(difficulty: DifficultyKey | 'all' = 'all'): MurdokuCase[] {
	if (difficulty === 'all') return allCases;
	return allCases.filter((entry) => entry.difficulty === difficulty);
}
