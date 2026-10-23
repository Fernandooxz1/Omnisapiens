import assert from 'node:assert/strict';
import test from 'node:test';
import {
	classifyCase,
	clueCost,
	complexityOf,
	generateCase,
	queryBudget,
	type GenerateInput
} from './generate.ts';
import { MURDOKU_THEMES } from './themes.ts';
import { validateCase } from './validate.ts';

const theme = MURDOKU_THEMES[0];

function input(size: number, difficulty: GenerateInput['difficulty'], seed: number): GenerateInput {
	return {
		size,
		difficulty,
		number: 1,
		title: 'Prueba',
		setting: theme.setting,
		theme,
		seed
	};
}

test('la misma semilla produce el mismo caso', () => {
	const first = generateCase(input(5, 'very_easy', 4242));
	const second = generateCase(input(5, 'very_easy', 4242));

	assert.ok(first);
	assert.ok(second);
	assert.deepEqual(first.entry, second.entry);
	assert.equal(first.attempts, second.attempts);
});

test('genera un 5×5 publicable', () => {
	const generated = generateCase(input(5, 'very_easy', 4242));

	assert.ok(generated);
	assert.equal(generated.entry.size, 5);
	assert.equal(generated.entry.suspects.length, 4);
	assert.deepEqual(validateCase(generated.entry), []);
	assert.ok(generated.entry.meta.seed > 0);
	assert.equal(generated.entry.id, 'murdoku-001');
});

test('genera un 9×9 del nivel pedido', () => {
	const generated = generateCase(input(9, 'medium', 90210));

	assert.ok(generated);
	assert.equal(generated.entry.size, 9);
	assert.equal(generated.entry.difficulty, 'medium');
	assert.deepEqual(validateCase(generated.entry), []);
});

test('classifyCase respeta los umbrales de 7×7 y 9×9', () => {
	assert.equal(classifyCase(5, 99), 'very_easy');
	assert.equal(classifyCase(6, 99), 'easy');
	assert.equal(classifyCase(7, 2), 'easy');
	assert.equal(classifyCase(7, 3), 'medium');
	assert.equal(classifyCase(8, 99), 'medium');
	assert.equal(classifyCase(9, 3), 'medium');
	assert.equal(classifyCase(9, 4), 'hard');
	assert.equal(classifyCase(10, 0), 'hard');
	assert.equal(classifyCase(15, 0), 'hardcore');
});

test('complexityOf suma negativas, diagonales y el exceso de pistas', () => {
	const negative = { type: 'notSameRegion', a: 's1', b: 's2' } as const;
	const longDirection = {
		type: 'direction',
		who: 's1',
		dir: 'N',
		steps: 2,
		than: 's2'
	} as const;
	const shortDirection = { ...longDirection, steps: 1 } as const;
	const diagonal = { type: 'adjacent', a: 's1', b: 's2', diagonal: true } as const;

	assert.equal(clueCost(negative), 2);
	assert.equal(clueCost(longDirection), 1);
	assert.equal(clueCost(shortDirection), 0);
	assert.equal(clueCost(diagonal), 1);

	const region = { type: 'region', who: 's1', region: 0 } as const;
	const crowded = Array.from({ length: 7 }, () => region);
	assert.equal(complexityOf(crowded, 5), 1);
});

test('los tableros grandes usan un presupuesto de nodos finito', () => {
	assert.equal(queryBudget(9), Number.POSITIVE_INFINITY);
	assert.ok(Number.isFinite(queryBudget(10)));
	assert.ok(Number.isFinite(queryBudget(15)));
});

test('genera un 10×10 que se valida dentro del presupuesto', () => {
	const generated = generateCase({ ...input(10, 'hard', 5150), deadline: Date.now() + 30_000 });

	assert.ok(generated);
	assert.equal(generated.entry.size, 10);
	assert.equal(generated.entry.difficulty, 'hard');
	assert.deepEqual(validateCase(generated.entry), []);
});
