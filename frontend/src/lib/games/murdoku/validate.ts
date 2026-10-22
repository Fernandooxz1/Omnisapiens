import type { Cell } from '../types.ts';
import { cellKey, holds, insideGrid, killerOf } from './rules.ts';
import { solve } from './solver.ts';
import type { Clue, MurdokuCase } from './types.ts';

/** Errores legibles en español; lista vacía = caso publicable. */
export function validateCase(entry: MurdokuCase): string[] {
	const errors: string[] = [];
	const size = entry.grid.size;

	if (entry.game !== 'murdoku') errors.push('El juego del caso debe ser "murdoku".');

	if (!Number.isInteger(size) || size < 5 || size > 15) {
		errors.push(`Tamaño inválido (${size}): la grilla va de 5 a 15.`);
	}

	if (entry.size !== size) {
		errors.push(`meta.size (${entry.size}) no coincide con grid.size (${size}).`);
	}

	if (!insideGrid(entry, entry.victim)) {
		errors.push('La víctima está fuera de la grilla.');
	}

	validateRegions(entry, errors);
	validateProps(entry, errors);

	const suspectIds = validateSuspects(entry, errors);
	validateSolution(entry, suspectIds, errors);
	validateKiller(entry, suspectIds, errors);

	// El solver solo corre si la estructura está sana: si no, el ruido tapa el error real.
	if (errors.length === 0) {
		const solutions = solve(entry, 2);
		if (solutions.length === 0) {
			errors.push('El caso no tiene solución con estas pistas.');
		} else if (solutions.length > 1) {
			errors.push('El caso tiene más de una solución: las pistas no alcanzan.');
		}
	}

	return errors;
}

/** Agrega los problemas del catálogo: IDs, títulos y números repetidos. */
export function validateCatalog(cases: MurdokuCase[]): string[] {
	const errors: string[] = [];
	const ids = new Set<string>();
	const titles = new Set<string>();
	const numbers = new Set<number>();

	for (const entry of cases) {
		for (const error of validateCase(entry)) errors.push(`${entry.id}: ${error}`);

		if (ids.has(entry.id)) errors.push(`${entry.id}: id duplicado.`);
		ids.add(entry.id);

		const title = entry.title.trim().toLowerCase();
		if (titles.has(title)) errors.push(`${entry.id}: título duplicado ("${entry.title}").`);
		titles.add(title);

		if (numbers.has(entry.number)) {
			errors.push(`${entry.id}: número de caso duplicado (${entry.number}).`);
		}
		numbers.add(entry.number);
	}

	return errors;
}

function validateRegions(entry: MurdokuCase, errors: string[]): void {
	const size = entry.grid.size;
	const regionList = entry.grid.regionList;

	if (regionList.length < 4 || regionList.length > 6) {
		errors.push(`Hay ${regionList.length} regiones: van de 4 a 6.`);
	}

	const declared = new Set<number>();
	for (const region of regionList) {
		if (declared.has(region.id)) errors.push(`Región duplicada: ${region.id}.`);
		declared.add(region.id);
	}

	if (!isMatrix(entry.grid.regions, size)) {
		errors.push('La matriz de regiones no mide N×N.');
		return;
	}

	const used = new Set<number>();
	for (let row = 0; row < size; row += 1) {
		for (let col = 0; col < size; col += 1) {
			const region = entry.grid.regions[row][col];
			if (!Number.isInteger(region) || !declared.has(region)) {
				errors.push(`La celda (${row}, ${col}) tiene una región inválida (${region}).`);
				continue;
			}
			used.add(region);
		}
	}

	for (const region of regionList) {
		if (!used.has(region.id)) {
			errors.push(`La región ${region.id} (${region.name}) no tiene celdas.`);
		} else if (!isRegionContiguous(entry, region.id)) {
			errors.push(`La región ${region.id} (${region.name}) no es contigua.`);
		}
	}
}

function isRegionContiguous(entry: MurdokuCase, region: number): boolean {
	const size = entry.grid.size;
	const cells: Cell[] = [];

	for (let row = 0; row < size; row += 1) {
		for (let col = 0; col < size; col += 1) {
			if (entry.grid.regions[row][col] === region) cells.push({ row, col });
		}
	}

	if (cells.length === 0) return false;

	const seen = new Set<string>([cellKey(cells[0])]);
	const queue: Cell[] = [cells[0]];

	while (queue.length > 0) {
		const cell = queue.pop() as Cell;
		const neighbours: Cell[] = [
			{ row: cell.row - 1, col: cell.col },
			{ row: cell.row + 1, col: cell.col },
			{ row: cell.row, col: cell.col - 1 },
			{ row: cell.row, col: cell.col + 1 }
		];

		for (const next of neighbours) {
			const key = cellKey(next);
			if (seen.has(key)) continue;
			if (!insideGrid(entry, next)) continue;
			if (entry.grid.regions[next.row][next.col] !== region) continue;
			seen.add(key);
			queue.push(next);
		}
	}

	return seen.size === cells.length;
}

function validateProps(entry: MurdokuCase, errors: string[]): void {
	const ids = new Set<string>();
	const cells = new Set<string>();

	for (const prop of entry.grid.props) {
		if (ids.has(prop.id)) errors.push(`Objeto duplicado: ${prop.id}.`);
		ids.add(prop.id);

		if (!insideGrid(entry, prop)) {
			errors.push(`El objeto ${prop.id} (${prop.name}) está fuera de la grilla.`);
			continue;
		}

		const key = cellKey(prop);
		if (cells.has(key)) errors.push(`Dos objetos ocupan la celda (${key}).`);
		cells.add(key);
	}

	// El generador evita objetos sobre personas: el tablero resuelto se lee limpio.
	for (const suspect of entry.suspects) {
		const cell = entry.solution[suspect.id];
		if (cell && cells.has(cellKey(cell))) {
			errors.push(`El objeto de la celda (${cellKey(cell)}) pisa a ${suspect.name} en la solución.`);
		}
	}
}

function validateSuspects(entry: MurdokuCase, errors: string[]): Set<string> {
	const expected = entry.grid.size - 1;
	const ids = new Set<string>();
	const initials = new Set<string>();

	if (entry.suspects.length !== expected) {
		errors.push(
			`Hay ${entry.suspects.length} sospechosos: el tablero ${entry.grid.size}×${entry.grid.size} necesita ${expected}.`
		);
	}

	for (const suspect of entry.suspects) {
		if (ids.has(suspect.id)) errors.push(`Sospechoso duplicado: ${suspect.id}.`);
		ids.add(suspect.id);

		const initial = suspect.initial.trim().toUpperCase();
		if (!initial) {
			errors.push(`El sospechoso ${suspect.id} no tiene inicial.`);
		} else if (initials.has(initial)) {
			errors.push(`La inicial "${initial}" se repite.`);
		} else {
			initials.add(initial);
		}

		if (suspect.clues.length < 1 || suspect.clues.length > 2) {
			errors.push(`${suspect.name} tiene ${suspect.clues.length} pistas: van de 1 a 2.`);
		}
	}

	for (const suspect of entry.suspects) {
		for (const clue of suspect.clues) {
			for (const error of clueErrors(clue, entry, ids)) {
				errors.push(`${suspect.name}: ${error}`);
			}
		}
	}

	return ids;
}

function clueErrors(clue: Clue, entry: MurdokuCase, suspectIds: Set<string>): string[] {
	const errors: string[] = [];
	const regionCount = entry.grid.regionList.length;
	const refs: string[] = [];

	switch (clue.type) {
		case 'region':
		case 'notRegion':
			if (!Number.isInteger(clue.region) || clue.region < 0 || clue.region >= regionCount) {
				errors.push(`la pista apunta a una región inexistente (${clue.region}).`);
			}
			refs.push(clue.who);
			break;

		case 'direction':
			if (!Number.isInteger(clue.steps) || clue.steps < 1) {
				errors.push(`la distancia de la pista debe ser 1 o más (${clue.steps}).`);
			}
			refs.push(clue.who, clue.than);
			break;

		case 'adjacent':
		case 'sameRegion':
		case 'notSameRegion':
			refs.push(clue.a, clue.b);
			break;

		case 'nearProp':
			if (!entry.grid.props.some((prop) => prop.id === clue.prop)) {
				errors.push(`la pista menciona un objeto inexistente (${clue.prop}).`);
			}
			refs.push(clue.who);
			break;

		case 'rowEdge':
		case 'colEdge':
			refs.push(clue.who);
			break;
	}

	for (const ref of refs) {
		if (!suspectIds.has(ref)) errors.push(`la pista menciona a un sospechoso inexistente (${ref}).`);
	}

	return errors;
}

function validateSolution(entry: MurdokuCase, suspectIds: Set<string>, errors: string[]): void {
	const cells = new Set<string>();
	const rows = new Set<number>();
	const cols = new Set<number>();

	for (const suspect of entry.suspects) {
		const cell = entry.solution[suspect.id];

		if (!cell) {
			errors.push(`${suspect.name} no tiene celda en la solución.`);
			continue;
		}

		if (!insideGrid(entry, cell)) {
			errors.push(`La celda de ${suspect.name} está fuera de la grilla.`);
			continue;
		}

		if (cell.row === entry.victim.row || cell.col === entry.victim.col) {
			errors.push(`${suspect.name} ocupa la fila o la columna de la víctima.`);
		}

		const key = cellKey(cell);
		if (cells.has(key)) errors.push(`Dos sospechosos comparten la celda (${key}).`);
		cells.add(key);

		if (rows.has(cell.row)) errors.push(`Dos sospechosos comparten la fila ${cell.row}.`);
		rows.add(cell.row);

		if (cols.has(cell.col)) errors.push(`Dos sospechosos comparten la columna ${cell.col}.`);
		cols.add(cell.col);
	}

	const extra = Object.keys(entry.solution).filter((id) => !suspectIds.has(id));
	if (extra.length > 0) {
		errors.push(`La solución menciona sospechosos que no existen: ${extra.join(', ')}.`);
	}

	for (const suspect of entry.suspects) {
		for (const [index, clue] of suspect.clues.entries()) {
			if (!holds(clue, entry.solution, entry)) {
				errors.push(`${suspect.name}: la pista ${index + 1} no se cumple en la solución.`);
			}
		}
	}
}

function validateKiller(entry: MurdokuCase, suspectIds: Set<string>, errors: string[]): void {
	if (!suspectIds.has(entry.killer)) {
		errors.push(`El asesino declarado (${entry.killer}) no es un sospechoso.`);
		return;
	}

	const actual = killerOf(entry, entry.solution);
	if (actual === entry.killer) return;

	const nameOf = (id: string | null) =>
		entry.suspects.find((suspect) => suspect.id === id)?.name ?? id ?? 'nadie';
	errors.push(
		`El asesino declarado es ${nameOf(entry.killer)}, pero la solución deja a ${nameOf(actual)} a solas con la víctima.`
	);
}

function isMatrix(matrix: number[][], size: number): boolean {
	if (!Array.isArray(matrix) || matrix.length !== size) return false;
	return matrix.every((row) => Array.isArray(row) && row.length === size);
}
