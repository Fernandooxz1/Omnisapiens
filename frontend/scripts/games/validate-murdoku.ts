import { fixtureCases } from '../../src/lib/games/murdoku/fixtures.ts';
import { allCases } from '../../src/lib/games/murdoku/cases/index.ts';
import type { MurdokuCase } from '../../src/lib/games/murdoku/types.ts';
import { validateCatalog } from '../../src/lib/games/murdoku/validate.ts';

const DIFFICULTY: Record<string, string> = {
	very_easy: 'muy fácil',
	easy: 'fácil',
	medium: 'medio',
	hard: 'difícil',
	very_hard: 'muy difícil',
	hardcore: 'hardcore'
};

const usage = 'Uso: npm run games:validate -- [--fixtures | --all | --id <caso>]';
const args = process.argv.slice(2);
const all = args.includes('--all');
const fixtures = args.includes('--fixtures');
const idIndex = args.indexOf('--id');
const id = idIndex === -1 ? null : (args[idIndex + 1] ?? '');

if (!all && !fixtures && !id) {
	console.error(usage);
	process.exit(1);
}

if (id !== null && !id) {
	console.error('Falta el id después de --id.');
	process.exit(1);
}

// El catálogo publicado son los casos de `cases/`; `--fixtures` valida los de prueba.
const source: MurdokuCase[] = fixtures ? fixtureCases : allCases;
const selected = id ? source.filter((entry) => entry.id === id) : source;

if (selected.length === 0) {
	console.error(`No hay ningún caso con id "${id}".`);
	process.exit(1);
}

const problems = validateCatalog(selected);
const byId = new Map<string, string[]>();

for (const problem of problems) {
	const separator = problem.indexOf(': ');
	const key = separator === -1 ? '' : problem.slice(0, separator);
	const message = separator === -1 ? problem : problem.slice(separator + 2);
	const list = byId.get(key) ?? [];
	list.push(message);
	byId.set(key, list);
}

console.log(`Validando ${selected.length} caso${selected.length === 1 ? '' : 's'}…`);

let failed = 0;

for (const entry of selected) {
	const caseProblems = byId.get(entry.id) ?? [];

	if (caseProblems.length === 0) {
		const difficulty = DIFFICULTY[entry.difficulty] ?? entry.difficulty;
		console.log(`  ✓ ${entry.id} · ${entry.title} (${entry.size}×${entry.size}, ${difficulty})`);
		continue;
	}

	failed += 1;
	console.log(`  ✗ ${entry.id} · ${entry.title}`);
	for (const message of caseProblems) console.log(`      - ${message}`);
}

console.log('');

if (problems.length === 0) {
	console.log(`${selected.length} caso${selected.length === 1 ? '' : 's'} válido${selected.length === 1 ? '' : 's'}.`);
} else {
	console.error(`${failed} de ${selected.length} casos con errores (${problems.length} en total).`);
	process.exitCode = 1;
}
