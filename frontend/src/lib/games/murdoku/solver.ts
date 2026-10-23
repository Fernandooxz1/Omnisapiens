import type { Cell } from '../types.ts';
import { allClues, holds, killerOf, type Assignment } from './rules.ts';
import type { Clue, MurdokuCase } from './types.ts';

/**
 * Solver de Murdoku: dominios como bitsets de celdas, consistencia de arcos
 * (AC-3) entre pistas binarias y una pasada global que propaga filas/columnas
 * únicas y la regla del asesino. El backtracking solo trabaja donde la
 * propagación no alcanza; sin esto, un tablero de 15×15 no termina.
 */

const WORD_BITS = 32;

/** Relación binaria entre dos celdas: `a.row = b.row + delta` o el equivalente en columnas. */
type PairKind =
	| 'rowDelta'
	| 'colDelta'
	| 'diagonal'
	| 'orthogonal'
	| 'sameRegion'
	| 'notSameRegion';

interface CompiledPair {
	a: number;
	b: number;
	/** Por cada celda de `a`, las celdas de `b` que cumplen la pista. */
	supportAB: Uint32Array;
	/** Por cada celda de `b`, las celdas de `a` que cumplen la pista. */
	supportBA: Uint32Array;
}

interface Compiled {
	size: number;
	cells: number;
	ids: string[];
	domains: Uint32Array[];
	pairs: CompiledPair[];
	rowMasks: Uint32Array[];
	colMasks: Uint32Array[];
	regionMask: Uint32Array;
	/** Sospechoso → pares binarios en los que participa. */
	adjacency: number[][];
}

function emptyMask(words: number): Uint32Array {
	return new Uint32Array(words);
}

function setBit(mask: Uint32Array, bit: number): void {
	mask[bit >>> 5] |= 1 << (bit & 31);
}

function hasBit(mask: Uint32Array, bit: number): boolean {
	return (mask[bit >>> 5] & (1 << (bit & 31))) !== 0;
}

function isSingleton(mask: Uint32Array): boolean {
	let seen = false;

	for (let word = 0; word < mask.length; word += 1) {
		let bits = mask[word];
		while (bits !== 0) {
			if (seen) return false;
			seen = true;
			bits &= bits - 1;
		}
	}

	return seen;
}

function orInto(dest: Uint32Array, mask: Uint32Array): void {
	for (let word = 0; word < dest.length; word += 1) dest[word] |= mask[word];
}

function isEmpty(mask: Uint32Array): boolean {
	for (let word = 0; word < mask.length; word += 1) {
		if (mask[word] !== 0) return false;
	}
	return true;
}

function popcount(mask: Uint32Array): number {
	let total = 0;
	for (let word = 0; word < mask.length; word += 1) {
		let bits = mask[word];
		while (bits !== 0) {
			bits &= bits - 1;
			total += 1;
		}
	}
	return total;
}

function singleCell(mask: Uint32Array): number {
	for (let word = 0; word < mask.length; word += 1) {
		const bits = mask[word];
		if (bits === 0) continue;
		return (word << 5) + (31 - Math.clz32(bits & -bits));
	}
	return -1;
}

function intersects(dest: Uint32Array, mask: Uint32Array): boolean {
	for (let word = 0; word < dest.length; word += 1) {
		if ((dest[word] & mask[word]) !== 0) return true;
	}
	return false;
}

/** `true` si `dest` cambió; deja solo las celdas presentes en `mask`. */
function intersectInto(dest: Uint32Array, mask: Uint32Array): boolean {
	let changed = false;
	for (let word = 0; word < dest.length; word += 1) {
		const next = (dest[word] & mask[word]) >>> 0;
		if (next !== dest[word]) {
			dest[word] = next;
			changed = true;
		}
	}
	return changed;
}

function removeInto(dest: Uint32Array, mask: Uint32Array): boolean {
	let changed = false;
	for (let word = 0; word < dest.length; word += 1) {
		const next = (dest[word] & ~mask[word]) >>> 0;
		if (next !== dest[word]) {
			dest[word] = next;
			changed = true;
		}
	}
	return changed;
}

/**
 * Tablas de soporte por relación. Dependen solo de la grilla, así que se
 * memoizan por `grid`: durante la generación el mismo tablero se resuelve
 * decenas de veces y reconstruirlas dominaría el tiempo.
 */
class SupportCache {
	private readonly table = new Map<string, Uint32Array>();
	private readonly regionCells = new Map<number, number[]>();
	readonly size: number;
	private readonly regions: number[][];

	constructor(size: number, regions: number[][]) {
		this.size = size;
		this.regions = regions;
	}

	get(kind: PairKind, delta: number): Uint32Array {
		const key = `${kind}:${delta}`;
		const found = this.table.get(key);
		if (found) return found;

		const built = this.build(kind, delta);
		this.table.set(key, built);
		return built;
	}

	private build(kind: PairKind, delta: number): Uint32Array {
		const { size } = this;
		const cells = size * size;
		const words = Math.ceil(cells / WORD_BITS);
		const table = new Uint32Array(cells * words);

		const mark = (offset: number, cell: number) => {
			table[offset + (cell >>> 5)] |= 1 << (cell & 31);
		};

		for (let row = 0; row < size; row += 1) {
			for (let col = 0; col < size; col += 1) {
				const offset = (row * size + col) * words;

				switch (kind) {
					case 'rowDelta': {
						const target = row - delta;
						if (target < 0 || target >= size) break;
						for (let next = 0; next < size; next += 1) mark(offset, target * size + next);
						break;
					}
					case 'colDelta': {
						const target = col - delta;
						if (target < 0 || target >= size) break;
						for (let next = 0; next < size; next += 1) mark(offset, next * size + target);
						break;
					}
					case 'diagonal':
					case 'orthogonal': {
						for (let dr = -1; dr <= 1; dr += 1) {
							for (let dc = -1; dc <= 1; dc += 1) {
								if (dr === 0 && dc === 0) continue;
								if (kind === 'orthogonal' && dr !== 0 && dc !== 0) continue;
								const targetRow = row + dr;
								const targetCol = col + dc;
								if (targetRow < 0 || targetRow >= size) continue;
								if (targetCol < 0 || targetCol >= size) continue;
								mark(offset, targetRow * size + targetCol);
							}
						}
						break;
					}
					case 'sameRegion': {
						for (const cell of this.cellsOfRegion(this.regions[row][col])) {
							mark(offset, cell);
						}
						break;
					}
					case 'notSameRegion': {
						for (let other = 0; other < cells; other += 1) {
							if (this.regions[Math.floor(other / size)][other % size] !== this.regions[row][col]) {
								mark(offset, other);
							}
						}
						break;
					}
				}
			}
		}

		return table;
	}

	private cellsOfRegion(region: number): number[] {
		const known = this.regionCells.get(region);
		if (known) return known;

		const { size } = this;
		const list: number[] = [];
		for (let row = 0; row < size; row += 1) {
			for (let col = 0; col < size; col += 1) {
				if (this.regions[row][col] === region) list.push(row * size + col);
			}
		}

		this.regionCells.set(region, list);
		return list;
	}
}

const supportCaches = new WeakMap<MurdokuCase['grid'], SupportCache>();

function supportCacheFor(entry: MurdokuCase): SupportCache {
	const known = supportCaches.get(entry.grid);
	if (known && known.size === entry.grid.size) return known;

	const cache = new SupportCache(entry.grid.size, entry.grid.regions);
	supportCaches.set(entry.grid, cache);
	return cache;
}

function compile(entry: MurdokuCase): Compiled {
	const size = entry.grid.size;
	const cells = size * size;
	const words = Math.ceil(cells / WORD_BITS);
	const ids = entry.suspects.map((suspect) => suspect.id);
	const indexOf = new Map(ids.map((id, index) => [id, index]));
	const supports = supportCacheFor(entry);

	const rowMasks = Array.from({ length: size }, () => emptyMask(words));
	const colMasks = Array.from({ length: size }, () => emptyMask(words));
	// La víctima ocupa su fila y su columna: ningún sospechoso puede usarlas.
	const base = emptyMask(words);

	for (let row = 0; row < size; row += 1) {
		for (let col = 0; col < size; col += 1) {
			const cell = row * size + col;
			setBit(rowMasks[row], cell);
			setBit(colMasks[col], cell);
			if (row !== entry.victim.row && col !== entry.victim.col) setBit(base, cell);
		}
	}

	const regionMasks = new Map<number, Uint32Array>();
	const regionMaskOf = (region: number): Uint32Array => {
		const found = regionMasks.get(region);
		if (found) return found;

		const mask = emptyMask(words);
		for (let row = 0; row < size; row += 1) {
			for (let col = 0; col < size; col += 1) {
				if (entry.grid.regions[row][col] === region) setBit(mask, row * size + col);
			}
		}

		regionMasks.set(region, mask);
		return mask;
	};

	const domains = ids.map(() => base.slice());
	const pairs: CompiledPair[] = [];
	const seen = new Set<string>();
	const adjacency: number[][] = ids.map(() => []);

	const addPair = (a: string, b: string, kind: PairKind, delta: number) => {
		const ai = indexOf.get(a);
		const bi = indexOf.get(b);
		if (ai === undefined || bi === undefined || ai === bi) return;

		const key = `${ai}|${bi}|${kind}|${delta}`;
		if (seen.has(key)) return;
		seen.add(key);

		const pairIndex = pairs.length;
		pairs.push({ a: ai, b: bi, supportAB: supports.get(kind, delta), supportBA: supports.get(kind, -delta) });
		adjacency[ai].push(pairIndex);
		adjacency[bi].push(pairIndex);
	};

	for (const suspect of entry.suspects) {
		const owner = indexOf.get(suspect.id);
		if (owner === undefined) continue;

		for (const clue of suspect.clues) {
			switch (clue.type) {
				case 'region':
					intersectInto(domains[owner], regionMaskOf(clue.region));
					break;
				case 'notRegion':
					removeInto(domains[owner], regionMaskOf(clue.region));
					break;
				case 'nearProp': {
					const prop = entry.grid.props.find((candidate) => candidate.id === clue.prop);
					if (!prop) {
						domains[owner].fill(0);
						break;
					}
					const cell = prop.row * size + prop.col;
					intersectInto(domains[owner], supports.get('orthogonal', 0).subarray(cell * words, (cell + 1) * words));
					break;
				}
				case 'rowEdge':
					intersectInto(domains[owner], clue.edge === 'top' ? rowMasks[0] : rowMasks[size - 1]);
					break;
				case 'colEdge':
					intersectInto(domains[owner], clue.edge === 'left' ? colMasks[0] : colMasks[size - 1]);
					break;
				case 'direction': {
					if (clue.dir === 'N') addPair(clue.who, clue.than, 'rowDelta', -clue.steps);
					if (clue.dir === 'S') addPair(clue.who, clue.than, 'rowDelta', clue.steps);
					if (clue.dir === 'W') addPair(clue.who, clue.than, 'colDelta', -clue.steps);
					if (clue.dir === 'E') addPair(clue.who, clue.than, 'colDelta', clue.steps);
					break;
				}
				case 'adjacent':
					addPair(clue.a, clue.b, clue.diagonal ? 'diagonal' : 'orthogonal', 0);
					break;
				case 'sameRegion':
					addPair(clue.a, clue.b, 'sameRegion', 0);
					break;
				case 'notSameRegion':
					addPair(clue.a, clue.b, 'notSameRegion', 0);
					break;
			}
		}
	}

	return {
		size,
		cells,
		ids,
		domains,
		pairs,
		rowMasks,
		colMasks,
		regionMask: regionMaskOf(entry.grid.regions[entry.victim.row][entry.victim.col]),
		adjacency
	};
}

/** Deja en `domA` solo las celdas con soporte en `domB`. */
function revise(domA: Uint32Array, domB: Uint32Array, support: Uint32Array): boolean {
	const words = domA.length;
	let changed = false;

	for (let word = 0; word < words; word += 1) {
		let bits = domA[word];
		if (bits === 0) continue;

		while (bits !== 0) {
			const bit = bits & -bits;
			bits ^= bit;
			const offset = ((word << 5) + (31 - Math.clz32(bit))) * words;
			let supported = false;

			for (let other = 0; other < words; other += 1) {
				if ((domB[other] & support[offset + other]) !== 0) {
					supported = true;
					break;
				}
			}

			if (!supported) {
				domA[word] &= ~bit;
				changed = true;
			}
		}
	}

	return changed;
}

function propagate(compiled: Compiled, domains: Uint32Array[], seed?: number): boolean {
	const { pairs, adjacency, ids } = compiled;
	const queued = new Uint8Array(pairs.length * 2);
	const queue: number[] = [];
	const words = domains.length > 0 ? domains[0].length : 1;
	const scratch = {
		blocked: new Uint32Array(words),
		single: new Uint8Array(ids.length),
		cells: new Int32Array(ids.length)
	};

	const enqueue = (arc: number) => {
		if (queued[arc] !== 0) return;
		queued[arc] = 1;
		queue.push(arc);
	};

	const enqueueFor = (suspect: number) => {
		for (const pairIndex of adjacency[suspect]) {
			const pair = pairs[pairIndex];
			if (pair.b === suspect) enqueue(pairIndex * 2);
			if (pair.a === suspect) enqueue(pairIndex * 2 + 1);
		}
	};

	// Desde una rama solo cambió el dominio de `seed`: el resto ya era un punto
	// fijo, así que alcanza con revisar los arcos que lo tocan.
	if (seed === undefined) {
		for (let arc = 0; arc < pairs.length * 2; arc += 1) enqueue(arc);
	} else {
		enqueueFor(seed);
	}

	for (;;) {
		while (queue.length > 0) {
			const arc = queue.pop() as number;
			queued[arc] = 0;
			const pair = pairs[arc >>> 1];
			const forward = (arc & 1) === 0;
			const target = forward ? pair.a : pair.b;
			const changed = forward
				? revise(domains[pair.a], domains[pair.b], pair.supportAB)
				: revise(domains[pair.b], domains[pair.a], pair.supportBA);

			if (isEmpty(domains[target])) return false;
			if (changed) enqueueFor(target);
		}

		const global = propagateGlobal(compiled, domains, enqueueFor, scratch);
		if (global === 0) return false;
		if (global === 1) return true;
	}
}

/** Filas/columnas únicas y regla del asesino. `0` falla, `1` estable, `2` cambió. */
function propagateGlobal(
	compiled: Compiled,
	domains: Uint32Array[],
	enqueueFor: (suspect: number) => void,
	scratch: { blocked: Uint32Array; single: Uint8Array; cells: Int32Array }
): 0 | 1 | 2 {
	const { ids, size, rowMasks, colMasks, regionMask } = compiled;
	const { blocked, single, cells } = scratch;
	let changed = false;
	let rowsUsed = 0;
	let colsUsed = 0;
	let singles = 0;

	blocked.fill(0);

	for (let index = 0; index < ids.length; index += 1) {
		const mask = domains[index];
		if (!isSingleton(mask)) {
			single[index] = 0;
			continue;
		}

		const cell = singleCell(mask);
		const row = Math.floor(cell / size);
		const col = cell % size;
		if ((rowsUsed & (1 << row)) !== 0 || (colsUsed & (1 << col)) !== 0) return 0;

		single[index] = 1;
		cells[index] = cell;
		rowsUsed |= 1 << row;
		colsUsed |= 1 << col;
		singles += 1;
		orInto(blocked, rowMasks[row]);
		orInto(blocked, colMasks[col]);
	}

	if (singles > 0) {
		for (let index = 0; index < ids.length; index += 1) {
			if (single[index] !== 0) continue;
			if (!removeInto(domains[index], blocked)) continue;
			if (isEmpty(domains[index])) return 0;

			enqueueFor(index);
			changed = true;
		}
	}

	let killer = -1;
	let candidates = 0;
	let lastCandidate = -1;

	for (let index = 0; index < ids.length; index += 1) {
		if (!intersects(domains[index], regionMask)) continue;

		candidates += 1;
		lastCandidate = index;

		if (single[index] !== 0) {
			if (killer !== -1) return 0;
			killer = index;
		}
	}

	if (candidates === 0) return 0;

	if (killer !== -1) {
		for (let other = 0; other < ids.length; other += 1) {
			if (other === killer) continue;
			if (!removeInto(domains[other], regionMask)) continue;
			if (isEmpty(domains[other])) return 0;

			enqueueFor(other);
			changed = true;
		}
	} else if (candidates === 1) {
		if (intersectInto(domains[lastCandidate], regionMask)) {
			if (isEmpty(domains[lastCandidate])) return 0;

			enqueueFor(lastCandidate);
			changed = true;
		}
	}

	return changed ? 2 : 1;
}

function toAssignment(compiled: Compiled, domains: Uint32Array[]): Assignment {
	const assignment: Assignment = {};

	compiled.ids.forEach((id, index) => {
		const cell = singleCell(domains[index]);
		assignment[id] = { row: Math.floor(cell / compiled.size), col: cell % compiled.size };
	});

	return assignment;
}

interface SearchState {
	nodes: number;
	budget: number;
	exhausted: boolean;
}

function search(
	entry: MurdokuCase,
	compiled: Compiled,
	domains: Uint32Array[],
	limit: number,
	solutions: Assignment[],
	state: SearchState
): void {
	if (solutions.length >= limit || state.exhausted) return;

	state.nodes += 1;
	if (state.nodes > state.budget) {
		state.exhausted = true;
		return;
	}

	let pick = -1;
	let narrowest = Number.POSITIVE_INFINITY;

	for (let index = 0; index < compiled.ids.length; index += 1) {
		const count = popcount(domains[index]);
		if (count === 1) continue;
		if (count < narrowest) {
			narrowest = count;
			pick = index;
		}
	}

	if (pick === -1) {
		const assignment = toAssignment(compiled, domains);
		// Red de seguridad: la propagación debería bastar, pero una pista que se
		// escape no puede terminar publicada como solución.
		if (!allClues(entry).every((clue) => holds(clue, assignment, entry))) return;
		if (killerOf(entry, assignment) !== entry.killer) return;

		solutions.push(assignment);
		return;
	}

	const source = domains[pick];

	for (let cell = 0; cell < compiled.cells; cell += 1) {
		if (state.exhausted || solutions.length >= limit) return;
		if (!hasBit(source, cell)) continue;

		const next = domains.map((mask) => mask.slice());
		next[pick].fill(0);
		setBit(next[pick], cell);
		if (!propagate(compiled, next, pick)) continue;

		search(entry, compiled, next, limit, solutions, state);
	}
}

export interface SolveResult {
	solutions: Assignment[];
	/** El presupuesto de nodos se agotó antes de terminar: el conteo no es concluyente. */
	exhausted: boolean;
}

/**
 * Resuelve con un tope de nodos. El tope es determinista (no depende del reloj),
 * así que dos corridas con la misma semilla gastan los mismos nodos y deciden
 * lo mismo.
 */
export function solveWithin(entry: MurdokuCase, limit: number, budget: number): SolveResult {
	if (entry.suspects.length === 0) {
		return { solutions: killerOf(entry, {}) === entry.killer ? [{}] : [], exhausted: false };
	}

	const compiled = compile(entry);
	const domains = compiled.domains.map((mask) => mask.slice());
	const solutions: Assignment[] = [];
	const state: SearchState = { nodes: 0, budget, exhausted: false };

	if (!propagate(compiled, domains)) return { solutions, exhausted: false };
	search(entry, compiled, domains, limit, solutions, state);

	return { solutions, exhausted: state.exhausted };
}

/** Hasta `limit` soluciones; con el tope por defecto 2 alcanza para probar unicidad. */
export function solve(entry: MurdokuCase, limit = 2): Assignment[] {
	return solveWithin(entry, limit, Number.POSITIVE_INFINITY).solutions;
}

export function countSolutions(entry: MurdokuCase, limit = 2): number {
	return solve(entry, limit).length;
}
