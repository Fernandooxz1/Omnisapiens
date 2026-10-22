import type { Cell, DifficultyKey } from '../types.ts';
import { cellKey, holds, isAdjacent } from './rules.ts';
import { countSolutions, solve } from './solver.ts';
import type {
	Clue,
	MurdokuCase,
	MurdokuProp,
	MurdokuRegion,
	MurdokuSuspect,
	SuspectColor
} from './types.ts';
import type { MurdokuTheme } from './themes.ts';

export type Random = () => number;

/** PRNG determinista: la misma semilla reconstruye el mismo caso. */
export function mulberry32(seed: number): Random {
	let state = seed >>> 0;

	return () => {
		state = (state + 0x6d2b79f5) >>> 0;
		let value = state;
		value = Math.imul(value ^ (value >>> 15), value | 1);
		value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
		return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
	};
}

const SUSPECT_NAMES: readonly (readonly [string, string])[] = [
	['Alicia', 'A'],
	['Bruno', 'B'],
	['Carla', 'C'],
	['Diego', 'D'],
	['Elena', 'E'],
	['Fabián', 'F'],
	['Gabriela', 'G'],
	['Hugo', 'H'],
	['Irene', 'I'],
	['Julián', 'J'],
	['Karina', 'K'],
	['Lorenzo', 'L'],
	['Marta', 'M'],
	['Nicolás', 'N'],
	['Olivia', 'O']
];

const VICTIM_NAMES: readonly string[] = [
	'Vera',
	'Tomás',
	'Sofía',
	'Ramiro',
	'Pilar',
	'Nadia',
	'Óscar',
	'Lucía',
	'Simón',
	'Teresa'
];

const SUSPECT_COLORS: readonly SuspectColor[] = [
	'green',
	'blue',
	'yellow',
	'orange',
	'pink',
	'purple',
	'red'
];

interface Person {
	id: string;
	name: string;
	initial: string;
	color: SuspectColor;
	cell: Cell;
}

interface Layout {
	size: number;
	victim: { name: string; row: number; col: number };
	people: Person[];
	killer: string;
	regions: number[][];
	regionList: MurdokuRegion[];
	props: MurdokuProp[];
}

interface ScoredClue {
	clue: Clue;
	cost: number;
	key: string;
}

export interface GenerateInput {
	size: number;
	difficulty: DifficultyKey;
	number: number;
	title: string;
	setting: string;
	theme: MurdokuTheme;
	seed: number;
	maxAttempts?: number;
}

export interface GeneratedCase {
	entry: MurdokuCase;
	attempts: number;
}

/**
 * Complejidad según el diseño §4: negativas, direcciones largas, diagonales y
 * habitaciones compartidas; el exceso de pistas suma uno más.
 */
export function clueCost(clue: Clue): number {
	switch (clue.type) {
		case 'notRegion':
			return 1;
		case 'notSameRegion':
			return 2;
		case 'direction':
			return clue.steps >= 2 ? 1 : 0;
		case 'adjacent':
			return clue.diagonal ? 1 : 0;
		case 'sameRegion':
			return 1;
		default:
			return 0;
	}
}

export function complexityOf(clues: readonly Clue[], size: number): number {
	const total = clues.reduce((sum, clue) => sum + clueCost(clue), 0);
	return clues.length > size + 1 ? total + 1 : total;
}

/** Nivel que corresponde a un tamaño y una complejidad (diseño §4). */
export function classifyCase(size: number, complexity: number): DifficultyKey {
	switch (size) {
		case 5:
			return 'very_easy';
		case 6:
			return 'easy';
		case 7:
			return complexity <= 2 ? 'easy' : 'medium';
		case 8:
			return 'medium';
		case 9:
			return complexity <= 3 ? 'medium' : 'hard';
		case 10:
			return 'hard';
		case 12:
			return 'very_hard';
		default:
			return 'hardcore';
	}
}

/** Tope de complejidad para no salir del nivel cuando el tamaño admite dos. */
function complexityBudget(size: number, difficulty: DifficultyKey): number {
	if (size === 7 && difficulty === 'easy') return 2;
	if (size === 9 && difficulty === 'medium') return 3;
	return Number.POSITIVE_INFINITY;
}

const ESTIMATED_MINUTES: Record<string, number> = {
	'5:very_easy': 3,
	'6:easy': 4,
	'7:easy': 6,
	'7:medium': 7,
	'8:medium': 8,
	'9:medium': 10,
	'9:hard': 12,
	'10:hard': 14,
	'12:very_hard': 20,
	'14:hardcore': 28,
	'15:hardcore': 32
};

export function estimatedMinutes(size: number, difficulty: DifficultyKey): number {
	return ESTIMATED_MINUTES[`${size}:${difficulty}`] ?? (size <= 6 ? 4 : size <= 8 ? 8 : 12);
}

function randInt(rnd: Random, max: number): number {
	return Math.floor(rnd() * max);
}

function sample<T>(rnd: Random, list: readonly T[]): T {
	return list[randInt(rnd, list.length)];
}

function shuffle<T>(rnd: Random, list: readonly T[]): T[] {
	const copy = [...list];
	for (let index = copy.length - 1; index > 0; index -= 1) {
		const swap = randInt(rnd, index + 1);
		[copy[index], copy[swap]] = [copy[swap], copy[index]];
	}
	return copy;
}

function allCells(size: number): Cell[] {
	const cells: Cell[] = [];
	for (let row = 0; row < size; row += 1) {
		for (let col = 0; col < size; col += 1) cells.push({ row, col });
	}
	return cells;
}

function neighbours(cell: Cell, size: number): Cell[] {
	const result: Cell[] = [];
	if (cell.row > 0) result.push({ row: cell.row - 1, col: cell.col });
	if (cell.row < size - 1) result.push({ row: cell.row + 1, col: cell.col });
	if (cell.col > 0) result.push({ row: cell.row, col: cell.col - 1 });
	if (cell.col < size - 1) result.push({ row: cell.row, col: cell.col + 1 });
	return result;
}

function chooseVictim(rnd: Random, size: number, difficulty: DifficultyKey): Cell {
	const border: Cell[] = [];
	const inner: Cell[] = [];

	for (const cell of allCells(size)) {
		const onBorder =
			cell.row === 0 || cell.col === 0 || cell.row === size - 1 || cell.col === size - 1;
		(onBorder ? border : inner).push(cell);
	}

	if (difficulty === 'very_easy' || difficulty === 'easy') return sample(rnd, border);
	if (difficulty === 'hard' || difficulty === 'very_hard' || difficulty === 'hardcore') {
		return sample(rnd, inner.length > 0 ? inner : border);
	}
	return sample(rnd, [...border, ...inner]);
}

/** Crecimiento aleatorio desde semillas: cada región queda contigua por construcción. */
function growRegions(rnd: Random, size: number, count: number): number[][] {
	const regions = Array.from({ length: size }, () => new Array<number>(size).fill(-1));
	const seeds = shuffle(rnd, allCells(size)).slice(0, count);

	seeds.forEach((cell, id) => {
		regions[cell.row][cell.col] = id;
	});

	let assigned = seeds.length;

	while (assigned < size * size) {
		const frontier: { cell: Cell; region: number }[] = [];

		for (const cell of allCells(size)) {
			if (regions[cell.row][cell.col] !== -1) continue;
			const touching = neighbours(cell, size)
				.map((next) => regions[next.row][next.col])
				.filter((region) => region !== -1);
			if (touching.length === 0) continue;
			frontier.push({ cell, region: sample(rnd, touching) });
		}

		const step = sample(rnd, frontier);
		regions[step.cell.row][step.cell.col] = step.region;
		assigned += 1;
	}

	return regions;
}

function placeProps(rnd: Random, size: number, theme: MurdokuTheme, blocked: Cell[]): MurdokuProp[] {
	const blockedKeys = new Set(blocked.map(cellKey));
	const free = allCells(size).filter((cell) => !blockedKeys.has(cellKey(cell)));
	const wanted = 4 + randInt(rnd, 7);
	const catalogue = shuffle(rnd, theme.props).slice(0, Math.min(wanted, theme.props.length));
	const cells = shuffle(rnd, free).slice(0, catalogue.length);

	return cells.map((cell, index) => ({
		id: `p${index + 1}`,
		name: catalogue[index].name,
		icon: catalogue[index].icon,
		row: cell.row,
		col: cell.col
	}));
}

function buildLayout(
	rnd: Random,
	size: number,
	difficulty: DifficultyKey,
	theme: MurdokuTheme
): Layout | null {
	const victimCell = chooseVictim(rnd, size, difficulty);
	const rows = shuffle(
		rnd,
		Array.from({ length: size }, (_, index) => index).filter((row) => row !== victimCell.row)
	);
	const cols = shuffle(
		rnd,
		Array.from({ length: size }, (_, index) => index).filter((col) => col !== victimCell.col)
	);
	const names = shuffle(rnd, SUSPECT_NAMES).slice(0, size - 1);

	const people: Person[] = names.map(([name, initial], index) => ({
		id: `s${index + 1}`,
		name,
		initial,
		color: SUSPECT_COLORS[index % SUSPECT_COLORS.length],
		cell: { row: rows[index], col: cols[index] }
	}));

	const regionCount = 4 + randInt(rnd, 3);
	const regions = growRegions(rnd, size, regionCount);
	const regionList: MurdokuRegion[] = theme.regions
		.slice(0, regionCount)
		.map((name, id) => ({ id, name, tone: id % 6 }));

	const victimRegion = regions[victimCell.row][victimCell.col];
	const inside = people.filter(
		(person) => regions[person.cell.row][person.cell.col] === victimRegion
	);
	if (inside.length !== 1) return null;

	const props = placeProps(rnd, size, theme, [
		{ row: victimCell.row, col: victimCell.col },
		...people.map((person) => person.cell)
	]);

	return {
		size,
		victim: { name: sample(rnd, VICTIM_NAMES), row: victimCell.row, col: victimCell.col },
		people,
		killer: inside[0].id,
		regions,
		regionList,
		props
	};
}

function clueKey(clue: Clue): string {
	return JSON.stringify(clue);
}

/**
 * Pistas candidatas verdaderas sobre la solución. Se excluyen las que nombran
 * la región de la víctima: el asesino se deduce por eliminación, no por un aviso.
 */
function candidateClues(layout: Layout): Map<string, ScoredClue[]> {
	const pools = new Map<string, ScoredClue[]>();
	const victimRegion = layout.regions[layout.victim.row][layout.victim.col];

	const add = (owner: string, clue: Clue) => {
		const key = clueKey(clue);
		const pool = pools.get(owner) ?? [];
		if (pool.some((candidate) => candidate.key === key)) return;
		pool.push({ clue, key, cost: clueCost(clue) });
		pools.set(owner, pool);
	};

	for (const person of layout.people) {
		const region = layout.regions[person.cell.row][person.cell.col];

		if (region !== victimRegion) add(person.id, { type: 'region', who: person.id, region });
		for (let other = 0; other < layout.regionList.length; other += 1) {
			if (other === region || other === victimRegion) continue;
			add(person.id, { type: 'notRegion', who: person.id, region: other });
		}

		for (const than of layout.people) {
			if (than.id === person.id) continue;
			const rowDelta = person.cell.row - than.cell.row;
			const colDelta = person.cell.col - than.cell.col;
			add(person.id, {
				type: 'direction',
				who: person.id,
				dir: rowDelta < 0 ? 'N' : 'S',
				steps: Math.abs(rowDelta),
				than: than.id
			});
			add(person.id, {
				type: 'direction',
				who: person.id,
				dir: colDelta < 0 ? 'W' : 'E',
				steps: Math.abs(colDelta),
				than: than.id
			});
		}

		for (const prop of layout.props) {
			if (isAdjacent(person.cell, prop, false)) {
				add(person.id, { type: 'nearProp', who: person.id, prop: prop.id });
			}
		}

		if (person.cell.row === 0) {
			add(person.id, { type: 'rowEdge', who: person.id, edge: 'top' });
		}
		if (person.cell.row === layout.size - 1) {
			add(person.id, { type: 'rowEdge', who: person.id, edge: 'bottom' });
		}
		if (person.cell.col === 0) {
			add(person.id, { type: 'colEdge', who: person.id, edge: 'left' });
		}
		if (person.cell.col === layout.size - 1) {
			add(person.id, { type: 'colEdge', who: person.id, edge: 'right' });
		}
	}

	for (let first = 0; first < layout.people.length; first += 1) {
		for (let second = first + 1; second < layout.people.length; second += 1) {
			const a = layout.people[first];
			const b = layout.people[second];

			if (isAdjacent(a.cell, b.cell, true)) {
				add(a.id, { type: 'adjacent', a: a.id, b: b.id, diagonal: true });
				add(b.id, { type: 'adjacent', a: a.id, b: b.id, diagonal: true });
			}

			const same =
				layout.regions[a.cell.row][a.cell.col] === layout.regions[b.cell.row][b.cell.col];
			if (same) {
				add(a.id, { type: 'sameRegion', a: a.id, b: b.id });
				add(b.id, { type: 'sameRegion', a: a.id, b: b.id });
			} else {
				add(a.id, { type: 'notSameRegion', a: a.id, b: b.id });
				add(b.id, { type: 'notSameRegion', a: a.id, b: b.id });
			}
		}
	}

	return pools;
}

function provisionalCase(layout: Layout): MurdokuCase {
	const solution: Record<string, Cell> = {};
	for (const person of layout.people) solution[person.id] = person.cell;

	return {
		id: '',
		game: 'murdoku',
		number: 0,
		title: '',
		setting: '',
		difficulty: 'very_easy',
		size: layout.size,
		estimatedMinutes: 0,
		grid: {
			size: layout.size,
			regions: layout.regions,
			regionList: layout.regionList,
			props: layout.props
		},
		suspects: layout.people.map((person) => ({
			id: person.id,
			name: person.name,
			initial: person.initial,
			color: person.color,
			clues: []
		})),
		victim: layout.victim,
		solution,
		killer: layout.killer,
		meta: { seed: 0, clueCount: 0, negatives: 0, complexity: 0, generatedBy: 'generator' }
	};
}

function cluesOf(entry: MurdokuCase): Clue[] {
	return entry.suspects.flatMap((suspect) => suspect.clues);
}

function pickOpening(rnd: Random, pool: ScoredClue[], mode: 'low' | 'mid'): ScoredClue {
	const ranked = [...pool].sort((a, b) => {
		if (mode === 'mid') {
			return Math.abs(a.cost - 1) - Math.abs(b.cost - 1) || a.cost - b.cost;
		}
		return a.cost - b.cost;
	});

	// En los niveles con tope de complejidad la primera pista no gasta presupuesto.
	const pool0 =
		mode === 'low' ? ranked.filter((candidate) => candidate.cost === ranked[0].cost) : ranked;
	const window = Math.max(1, Math.ceil(pool0.length / 3));
	return pool0[randInt(rnd, window)];
}

/**
 * Elige la pista extra que separa la solución declarada de alguna alternativa
 * que el solver ya encontró. Entre las candidatas se queda con la que deja
 * menos soluciones: greedy que alcanza la unicidad con pocas pistas.
 */
function pickDiscriminating(
	rnd: Random,
	entry: MurdokuCase,
	pools: Map<string, ScoredClue[]>,
	used: Set<string>,
	budget: number
): { suspect: MurdokuSuspect; candidate: ScoredClue } | null {
	const ids = entry.suspects.map((suspect) => suspect.id);
	const alternatives = solve(entry, 2).filter((solution) =>
		ids.some(
			(id) =>
				solution[id]?.row !== entry.solution[id].row ||
				solution[id]?.col !== entry.solution[id].col
		)
	);
	if (alternatives.length === 0) return null;

	const options: { suspect: MurdokuSuspect; candidate: ScoredClue }[] = [];

	for (const suspect of entry.suspects) {
		if (suspect.clues.length >= 2) continue;

		for (const candidate of pools.get(suspect.id) ?? []) {
			if (used.has(candidate.key)) continue;

			const separates = alternatives.some(
				(alternative) => !holds(candidate.clue, alternative, entry)
			);
			if (!separates) continue;
			if (complexityOf([...cluesOf(entry), candidate.clue], entry.grid.size) > budget) continue;

			options.push({ suspect, candidate });
		}
	}

	if (options.length === 0) return null;

	// Greedy: entre las que separan, la que deja menos soluciones.
	const shortlist = shuffle(rnd, options).slice(0, 24);
	let best: { suspect: MurdokuSuspect; candidate: ScoredClue; count: number } | null = null;

	for (const option of shortlist) {
		option.suspect.clues.push(option.candidate.clue);
		const count = countSolutions(entry, 2);
		option.suspect.clues.pop();

		if (count === 0) continue;

		const better =
			!best ||
			count < best.count ||
			(count === best.count && option.candidate.cost < best.candidate.cost);
		if (better) best = { suspect: option.suspect, candidate: option.candidate, count };
	}

	if (!best) return null;
	return { suspect: best.suspect, candidate: best.candidate };
}

/** Elimina pistas extra sin romper la unicidad; cada sospechoso conserva la primera. */
function pruneExtras(rnd: Random, entry: MurdokuCase): void {
	const extras: { suspect: MurdokuSuspect; clue: Clue }[] = [];

	for (const suspect of entry.suspects) {
		for (let index = 1; index < suspect.clues.length; index += 1) {
			extras.push({ suspect, clue: suspect.clues[index] });
		}
	}

	for (const item of shuffle(rnd, extras)) {
		const index = item.suspect.clues.indexOf(item.clue);
		if (index <= 0) continue;

		item.suspect.clues.splice(index, 1);
		if (countSolutions(entry, 2) === 1) continue;
		item.suspect.clues.splice(index, 0, item.clue);
	}
}

function buildClues(
	rnd: Random,
	layout: Layout,
	difficulty: DifficultyKey,
	entry: MurdokuCase
): boolean {
	const pools = candidateClues(layout);
	const used = new Set<string>();
	const budget = complexityBudget(layout.size, difficulty);
	const openingMode =
		budget === Number.POSITIVE_INFINITY &&
		(difficulty === 'medium' ||
			difficulty === 'hard' ||
			difficulty === 'very_hard' ||
			difficulty === 'hardcore')
			? 'mid'
			: 'low';
	const openings = shuffle(rnd, layout.people);

	for (const person of openings) {
		const options = (pools.get(person.id) ?? []).filter((clue) => !used.has(clue.key));
		if (options.length === 0) return false;

		const chosen = pickOpening(rnd, options, openingMode);
		used.add(chosen.key);
		entry.suspects.find((suspect) => suspect.id === person.id)?.clues.push(chosen.clue);
	}

	let solutions = countSolutions(entry, 2);
	if (solutions === 0) return false;

	const maxRounds = 2 * (layout.size - 1);
	let round = 0;

	while (solutions > 1) {
		round += 1;
		if (round > maxRounds) return false;

		const extra = pickDiscriminating(rnd, entry, pools, used, budget);
		if (!extra) return false;

		extra.suspect.clues.push(extra.candidate.clue);
		used.add(extra.candidate.key);
		solutions = countSolutions(entry, 2);
	}

	pruneExtras(rnd, entry);
	return true;
}

/**
 * Intenta semillas derivadas hasta dar con un caso único y del nivel pedido.
 * La misma entrada produce siempre el mismo caso.
 */
export function generateCase(input: GenerateInput): GeneratedCase | null {
	const maxAttempts = input.maxAttempts ?? 80;

	for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
		const seed = (input.seed + attempt * 104729) >>> 0;
		const rnd = mulberry32(seed);
		const layout = buildLayout(rnd, input.size, input.difficulty, input.theme);
		if (!layout) continue;

		const entry = provisionalCase(layout);
		if (!buildClues(rnd, layout, input.difficulty, entry)) continue;

		const clues = cluesOf(entry);
		const complexity = complexityOf(clues, input.size);
		if (classifyCase(input.size, complexity) !== input.difficulty) continue;
		if (countSolutions(entry, 2) !== 1) continue;

		entry.id = `murdoku-${String(input.number).padStart(3, '0')}`;
		entry.number = input.number;
		entry.title = input.title;
		entry.setting = input.setting;
		entry.difficulty = input.difficulty;
		entry.estimatedMinutes = estimatedMinutes(input.size, input.difficulty);
		entry.meta = {
			seed,
			clueCount: clues.length,
			negatives: clues.filter(
				(clue) => clue.type === 'notRegion' || clue.type === 'notSameRegion'
			).length,
			complexity,
			generatedBy: 'generator'
		};

		return { entry, attempts: attempt + 1 };
	}

	return null;
}
