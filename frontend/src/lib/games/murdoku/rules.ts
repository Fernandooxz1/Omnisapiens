import type { Cell } from '../types.ts';
import type { Clue, MurdokuCase } from './types.ts';

/** Sospechoso → celda. Parcial mientras el solver poda. */
export type Assignment = Record<string, Cell>;

export function cellKey(cell: Cell): string {
	return `${cell.row},${cell.col}`;
}

export function cellFromKey(key: string): Cell {
	const [row, col] = key.split(',').map(Number);
	return { row, col };
}

export function insideGrid(entry: MurdokuCase, cell: Cell): boolean {
	return (
		Number.isInteger(cell.row) &&
		Number.isInteger(cell.col) &&
		cell.row >= 0 &&
		cell.row < entry.grid.size &&
		cell.col >= 0 &&
		cell.col < entry.grid.size
	);
}

/** -1 fuera de la grilla: así una celda inválida nunca comparte región. */
export function regionAt(entry: MurdokuCase, cell: Cell): number {
	if (!insideGrid(entry, cell)) return -1;
	return entry.grid.regions[cell.row][cell.col];
}

export function sameRegion(entry: MurdokuCase, a: Cell, b: Cell): boolean {
	const region = regionAt(entry, a);
	return region !== -1 && region === regionAt(entry, b);
}

export function isAdjacent(a: Cell, b: Cell, diagonal: boolean): boolean {
	const rowDelta = Math.abs(a.row - b.row);
	const colDelta = Math.abs(a.col - b.col);

	if (diagonal) return Math.max(rowDelta, colDelta) === 1;
	return rowDelta + colDelta === 1;
}

/** Desplazamiento de la pista: el eje libre queda en 0. */
export function directionDelta(dir: 'N' | 'S' | 'E' | 'W', steps: number): Cell {
	switch (dir) {
		case 'N':
			return { row: -steps, col: 0 };
		case 'S':
			return { row: steps, col: 0 };
		case 'E':
			return { row: 0, col: steps };
		case 'W':
			return { row: 0, col: -steps };
	}
}

function matchesDirection(from: Cell, to: Cell, dir: 'N' | 'S' | 'E' | 'W', steps: number): boolean {
	const delta = directionDelta(dir, steps);
	const rowOk = delta.row === 0 || from.row === to.row + delta.row;
	const colOk = delta.col === 0 || from.col === to.col + delta.col;
	return rowOk && colOk;
}

/**
 * `true`/`false` cuando la pista ya se puede decidir; `null` si le falta alguna
 * celda. La poda del solver usa `null` como "todavía puede ser".
 */
function evaluate(clue: Clue, assignment: Assignment, entry: MurdokuCase): boolean | null {
	switch (clue.type) {
		case 'region': {
			const cell = assignment[clue.who];
			if (!cell) return null;
			return regionAt(entry, cell) === clue.region;
		}

		case 'notRegion': {
			const cell = assignment[clue.who];
			if (!cell) return null;
			return regionAt(entry, cell) !== clue.region;
		}

		case 'direction': {
			const who = assignment[clue.who];
			const than = assignment[clue.than];
			if (!who || !than) return null;
			return matchesDirection(who, than, clue.dir, clue.steps);
		}

		case 'adjacent': {
			const a = assignment[clue.a];
			const b = assignment[clue.b];
			if (!a || !b) return null;
			return isAdjacent(a, b, clue.diagonal);
		}

		case 'sameRegion': {
			const a = assignment[clue.a];
			const b = assignment[clue.b];
			if (!a || !b) return null;
			return sameRegion(entry, a, b);
		}

		case 'notSameRegion': {
			const a = assignment[clue.a];
			const b = assignment[clue.b];
			if (!a || !b) return null;
			return !sameRegion(entry, a, b);
		}

		case 'nearProp': {
			const cell = assignment[clue.who];
			const prop = entry.grid.props.find((candidate) => candidate.id === clue.prop);
			if (!prop) return false;
			if (!cell) return null;
			return isAdjacent(cell, prop, false);
		}

		case 'rowEdge': {
			const cell = assignment[clue.who];
			if (!cell) return null;
			return cell.row === (clue.edge === 'top' ? 0 : entry.grid.size - 1);
		}

		case 'colEdge': {
			const cell = assignment[clue.who];
			if (!cell) return null;
			return cell.col === (clue.edge === 'left' ? 0 : entry.grid.size - 1);
		}
	}
}

/** Una asignación completa cumple la pista. Una celda faltante la vuelve falsa. */
export function holds(clue: Clue, assignment: Assignment, entry: MurdokuCase): boolean {
	return evaluate(clue, assignment, entry) === true;
}

/** `false` solo cuando la pista ya está rota; si falta información todavía puede ser. */
export function canHold(clue: Clue, partial: Assignment, entry: MurdokuCase): boolean {
	return evaluate(clue, partial, entry) !== false;
}

/** Las pistas de todos los sospechosos, sin dueño: al solver le da igual quién la firma. */
export function allClues(entry: MurdokuCase): Clue[] {
	return entry.suspects.flatMap((suspect) => suspect.clues);
}

/** El único sospechoso en la región de la víctima; `null` si hay cero o más de uno. */
export function killerOf(entry: MurdokuCase, assignment: Assignment): string | null {
	const victimRegion = regionAt(entry, { row: entry.victim.row, col: entry.victim.col });
	let found: string | null = null;

	for (const suspect of entry.suspects) {
		const cell = assignment[suspect.id];
		if (!cell || regionAt(entry, cell) !== victimRegion) continue;
		if (found) return null;
		found = suspect.id;
	}

	return found;
}

/** Celda libre para ese sospechoso: dentro de la grilla y sin chocar fila ni columna. */
export function isValidPlacement(
	entry: MurdokuCase,
	assignment: Assignment,
	suspectId: string,
	target: Cell
): boolean {
	if (!insideGrid(entry, target)) return false;
	if (target.row === entry.victim.row || target.col === entry.victim.col) return false;

	for (const [id, cell] of Object.entries(assignment)) {
		if (id === suspectId) continue;
		if (cell.row === target.row || cell.col === target.col) return false;
	}

	return true;
}
