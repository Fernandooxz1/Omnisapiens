import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { DifficultyKey } from '../../src/lib/games/types.ts';
import { generateCase } from '../../src/lib/games/murdoku/generate.ts';
import { MURDOKU_THEMES } from '../../src/lib/games/murdoku/themes.ts';
import type { MurdokuCase } from '../../src/lib/games/murdoku/types.ts';

interface Target {
	size: number;
	difficulty: DifficultyKey;
	count: number;
}

/** Distribución de la fase 2: 48 casos de 5×5 a 9×9. */
const STANDARD_TARGETS: readonly Target[] = [
	{ size: 5, difficulty: 'very_easy', count: 6 },
	{ size: 6, difficulty: 'easy', count: 8 },
	{ size: 7, difficulty: 'easy', count: 6 },
	{ size: 7, difficulty: 'medium', count: 6 },
	{ size: 8, difficulty: 'medium', count: 8 },
	{ size: 9, difficulty: 'medium', count: 10 },
	{ size: 9, difficulty: 'hard', count: 4 }
];

/** Batch grande: 14 casos de 10×10 a 15×15. */
const LARGE_TARGETS: readonly Target[] = [
	{ size: 10, difficulty: 'hard', count: 6 },
	{ size: 12, difficulty: 'very_hard', count: 4 },
	{ size: 14, difficulty: 'hardcore', count: 2 },
	{ size: 15, difficulty: 'hardcore', count: 2 }
];

/** Los casos grandes siguen la numeración del catálogo estándar. */
const STANDARD_CASES = 48;

const USAGE =
	'Uso: npm run games:generate -- --max-size 9 | --min-size 10 | --size <n> [--difficulty <nivel>] [--count <n>] [--seed <n>]';
const DIFFICULTY_LABEL: Record<DifficultyKey, string> = {
	very_easy: 'muy fácil',
	easy: 'fácil',
	medium: 'medio',
	hard: 'difícil',
	very_hard: 'muy difícil',
	hardcore: 'hardcore'
};
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');

/**
 * Presupuesto por caso. El determinismo lo garantiza el tope de nodos de
 * `generateCase`; este reloj solo evita que un caso patológico frene el batch.
 */
function caseBudget(size: number): number {
	if (size >= 14) return 60_000;
	if (size >= 10) return 30_000;
	return 20_000;
}

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

function quote(value: string): string {
	return `'${value.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`;
}

function isObject(value: Json): value is Record<string, Json> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** `null` cuando el valor merece varias líneas. */
function inline(value: Json): string | null {
	if (value === null) return 'null';
	if (typeof value === 'number' || typeof value === 'boolean') return String(value);
	if (typeof value === 'string') return quote(value);

	if (Array.isArray(value)) {
		if (value.every((item) => typeof item === 'number')) return `[${value.join(', ')}]`;
		const parts = value.map(inline);
		if (parts.every((part) => part !== null)) {
			const rendered = `[${parts.join(', ')}]`;
			if (rendered.length <= 92) return rendered;
		}
		return null;
	}

	const parts = Object.entries(value).map(([key, item]) => {
		const rendered = inline(item);
		return rendered === null ? null : `${key}: ${rendered}`;
	});
	if (!parts.every((part) => part !== null)) return null;

	const rendered = `{ ${parts.join(', ')} }`;
	return rendered.length <= 92 ? rendered : null;
}

function format(value: Json, indent: number): string {
	const flat = inline(value);
	if (flat !== null) return flat;

	const pad = '\t'.repeat(indent);
	const inner = '\t'.repeat(indent + 1);

	if (Array.isArray(value)) {
		const items = value.map((item) => `${inner}${format(item, indent + 1)}`);
		return `[\n${items.join(',\n')}\n${pad}]`;
	}

	const items = Object.entries(value).map(
		([key, item]) => `${inner}${key}: ${format(item, indent + 1)}`
	);
	return `{\n${items.join(',\n')}\n${pad}}`;
}

const args = process.argv.slice(2);

function valueOf(flag: string): string | null {
	const index = args.indexOf(flag);
	return index === -1 ? null : (args[index + 1] ?? '');
}

const maxSize = valueOf('--max-size');
const minSize = valueOf('--min-size');
const size = valueOf('--size');
const difficulty = valueOf('--difficulty') as DifficultyKey | null;
const count = valueOf('--count');
const seedArg = valueOf('--seed');

if (maxSize === null && minSize === null && size === null) {
	console.error(USAGE);
	process.exit(1);
}

// `--max-size 9` arma el catálogo estándar; de 10 en adelante, el batch grande.
const large = maxSize === null || Number(maxSize) >= 10;
let targets = (large ? LARGE_TARGETS : STANDARD_TARGETS).filter((target) => {
	if (maxSize !== null && target.size > Number(maxSize)) return false;
	if (minSize !== null && target.size < Number(minSize)) return false;
	return true;
});

if (size !== null) targets = targets.filter((target) => target.size === Number(size));
if (difficulty !== null) targets = targets.filter((target) => target.difficulty === difficulty);

if (count !== null) {
	if (targets.length !== 1) {
		console.error('--count necesita --size y --difficulty para apuntar a un solo grupo.');
		process.exit(1);
	}
	targets = targets.map((target) => ({ ...target, count: Number(count) }));
}

if (targets.length === 0) {
	console.error('No hay ningún grupo de casos que coincida con los argumentos.');
	process.exit(1);
}

const OUTPUT = resolve(
	ROOT,
	large ? 'src/lib/games/murdoku/cases/large.ts' : 'src/lib/games/murdoku/cases/standard.ts'
);
const EXPORT = large ? 'largeCases' : 'standardCases';
const COMMAND = large ? 'npm run games:generate -- --min-size 10' : 'npm run games:generate -- --max-size 9';

const baseSeed = seedArg === null ? 20261022 : Number(seedArg);
const cases: MurdokuCase[] = [];
const timings: { id: string; size: number; elapsed: number }[] = [];
const failures: Target[] = [];
const startedAt = Date.now();
let totalAttempts = 0;
let index = 0;

for (const target of targets) {
	for (let remaining = 0; remaining < target.count; remaining += 1) {
		const number = (large ? STANDARD_CASES : 0) + index + 1;
		const theme = MURDOKU_THEMES[index % MURDOKU_THEMES.length];
		const titleSlot = large
			? 6 + Math.floor(index / MURDOKU_THEMES.length)
			: Math.floor(index / MURDOKU_THEMES.length);
		const title = theme.titles[titleSlot % theme.titles.length];
		const caseStartedAt = Date.now();
		index += 1;

		const generated = generateCase({
			size: target.size,
			difficulty: target.difficulty,
			number,
			title,
			setting: theme.setting,
			theme,
			seed: (baseSeed + number * 7919) >>> 0,
			deadline: caseStartedAt + caseBudget(target.size)
		});

		if (!generated) {
			failures.push({ ...target, count: 1 });
			console.error(
				`  ✗ ${target.size}×${target.size} ${DIFFICULTY_LABEL[target.difficulty]} · sin caso dentro del presupuesto`
			);
			continue;
		}

		totalAttempts += generated.attempts;
		cases.push(generated.entry);

		const elapsed = Date.now() - caseStartedAt;
		timings.push({ id: generated.entry.id, size: target.size, elapsed });
		console.log(
			`  ✓ ${generated.entry.id} · ${generated.entry.title} (${target.size}×${target.size}, ${DIFFICULTY_LABEL[target.difficulty]}, ${generated.entry.meta.clueCount} pistas, complejidad ${generated.entry.meta.complexity}; ${generated.attempts} intento${generated.attempts === 1 ? '' : 's'}, ${elapsed} ms)`
		);
	}
}

const elapsed = Date.now() - startedAt;

console.log('');

const counts = new Map<string, number>();
for (const entry of cases) {
	const key = `${entry.size}×${entry.size} ${DIFFICULTY_LABEL[entry.difficulty]}`;
	counts.set(key, (counts.get(key) ?? 0) + 1);
}
for (const [key, value] of counts) console.log(`  ${key}: ${value}`);

console.log('');
console.log(
	`${cases.length} casos en ${(elapsed / 1000).toFixed(1)} s (${totalAttempts} intentos, ${totalAttempts - cases.length} reintentos).`
);

const largest = timings.reduce((biggest, item) => Math.max(biggest, item.size), 0);
const slowestRun = timings
	.filter((item) => item.size === largest)
	.map((item) => `${item.id} ${item.elapsed} ms`)
	.join(' · ');

if (slowestRun !== '') console.log(`Benchmark ${largest}×${largest}: ${slowestRun}.`);

if (failures.length > 0) {
	console.error(`${failures.length} casos no se pudieron generar; no se escribe el catálogo.`);
	process.exit(1);
}

const header = `import type { MurdokuCase } from '../types.ts';

/** Generado por \`${COMMAND}\` (semilla base ${baseSeed}). No editar a mano. */
export const ${EXPORT}: MurdokuCase[] = `;

await mkdir(dirname(OUTPUT), { recursive: true });
await writeFile(OUTPUT, `${header}${format(cases as unknown as Json, 0)};\n`, 'utf8');
console.log(`Escrito ${OUTPUT}`);
