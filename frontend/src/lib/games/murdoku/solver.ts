import type { Cell } from '../types.ts';
import { allClues, canHold, holds, killerOf, type Assignment } from './rules.ts';
import type { Clue, MurdokuCase } from './types.ts';

/**
 * Backtracking con máscaras de fila/columna, MRV y poda por pistas.
 * La víctima ocupa su fila y su columna desde el arranque.
 */
export function solve(entry: MurdokuCase, limit = 2): Assignment[] {
	const solutions: Assignment[] = [];

	if (entry.suspects.length === 0) {
		if (killerOf(entry, {}) === entry.killer) solutions.push({});
		return solutions;
	}

	search(
		entry,
		entry.suspects.map((suspect) => suspect.id),
		{},
		1 << entry.victim.row,
		1 << entry.victim.col,
		allClues(entry),
		limit,
		solutions
	);

	return solutions;
}

export function countSolutions(entry: MurdokuCase, limit = 2): number {
	return solve(entry, limit).length;
}

/** Con tope 2 alcanza para probar unicidad: el validador no necesita más. */
function search(
	entry: MurdokuCase,
	remaining: string[],
	assignment: Assignment,
	usedRows: number,
	usedCols: number,
	clues: Clue[],
	limit: number,
	solutions: Assignment[]
): void {
	if (solutions.length >= limit) return;

	if (remaining.length === 0) {
		const complete = clues.every((clue) => holds(clue, assignment, entry));
		if (complete && killerOf(entry, assignment) === entry.killer) {
			solutions.push({ ...assignment });
		}
		return;
	}

	let pick: { id: string; cells: Cell[] } | null = null;

	for (const id of remaining) {
		const cells = candidates(entry, id, assignment, usedRows, usedCols, clues);
		if (cells.length === 0) return;
		if (!pick || cells.length < pick.cells.length) pick = { id, cells };
	}

	if (!pick) return;

	const rest = remaining.filter((id) => id !== pick.id);

	for (const cell of pick.cells) {
		assignment[pick.id] = cell;
		search(
			entry,
			rest,
			assignment,
			usedRows | (1 << cell.row),
			usedCols | (1 << cell.col),
			clues,
			limit,
			solutions
		);
		if (solutions.length >= limit) break;
	}

	delete assignment[pick.id];
}

/** Celdas libres del sospechoso que no rompen ninguna pista decidible. */
function candidates(
	entry: MurdokuCase,
	id: string,
	assignment: Assignment,
	usedRows: number,
	usedCols: number,
	clues: Clue[]
): Cell[] {
	const size = entry.grid.size;
	const cells: Cell[] = [];

	for (let row = 0; row < size; row += 1) {
		if (usedRows & (1 << row)) continue;

		for (let col = 0; col < size; col += 1) {
			if (usedCols & (1 << col)) continue;

			assignment[id] = { row, col };
			const ok = clues.every((clue) => canHold(clue, assignment, entry));
			delete assignment[id];

			if (ok) cells.push({ row, col });
		}
	}

	return cells;
}
