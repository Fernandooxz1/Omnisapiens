import assert from 'node:assert/strict';
import test from 'node:test';
import { allCases } from './cases/index.ts';
import { fixtureCases } from './fixtures.ts';
import { countSolutions, solve, solveWithin } from './solver.ts';
import type { MurdokuCase } from './types.ts';

const [study, library] = fixtureCases;

test('solve encuentra la solución única de los casos de fixture', () => {
	assert.deepEqual(solve(study), [study.solution]);
	assert.deepEqual(solve(library), [library.solution]);
});

test('countSolutions respeta el tope pedido', () => {
	assert.equal(countSolutions(study, 1), 1);
	assert.equal(countSolutions(study, 2), 1);
});

test('solve devuelve cero soluciones con una pista falsa', () => {
	const broken: MurdokuCase = structuredClone(study);
	broken.suspects[0].clues = [{ type: 'region', who: 's1', region: 1 }];

	assert.equal(countSolutions(broken), 0);
});

test('solve detecta varias soluciones cuando faltan pistas', () => {
	const ambiguous: MurdokuCase = structuredClone(study);
	for (const suspect of ambiguous.suspects) suspect.clues = [];

	assert.equal(countSolutions(ambiguous, 1), 1);
	assert.equal(countSolutions(ambiguous, 2), 2);
});

test('el solver resuelve los tableros de 15×15 del catálogo', () => {
	const large = allCases.filter((entry) => entry.size === 15);

	assert.equal(large.length, 2);
	for (const entry of large) {
		assert.deepEqual(solve(entry), [entry.solution]);
		assert.equal(countSolutions(entry), 1);
	}
});

test('solveWithin avisa cuando el presupuesto de nodos no alcanza', () => {
	const ambiguous: MurdokuCase = structuredClone(study);
	for (const suspect of ambiguous.suspects) suspect.clues = [];

	const result = solveWithin(ambiguous, 2, 1);
	assert.equal(result.exhausted, true);
	assert.ok(result.solutions.length < 2);
});
