import assert from 'node:assert/strict';
import test from 'node:test';
import { fixtureCases } from './fixtures.ts';
import {
	canHold,
	cellFromKey,
	cellKey,
	directionDelta,
	holds,
	isAdjacent,
	isValidPlacement,
	killerOf,
	sameRegion
} from './rules.ts';
import type { Clue } from './types.ts';

const study = fixtureCases[0];
const solution = study.solution;

test('cellKey y cellFromKey son inversas', () => {
	assert.equal(cellKey({ row: 3, col: 1 }), '3,1');
	assert.deepEqual(cellFromKey('3,1'), { row: 3, col: 1 });
});

test('directionDelta mueve un solo eje', () => {
	assert.deepEqual(directionDelta('N', 2), { row: -2, col: 0 });
	assert.deepEqual(directionDelta('S', 1), { row: 1, col: 0 });
	assert.deepEqual(directionDelta('E', 3), { row: 0, col: 3 });
	assert.deepEqual(directionDelta('W', 1), { row: 0, col: -1 });
});

test('isAdjacent distingue lados y diagonales', () => {
	assert.equal(isAdjacent({ row: 0, col: 0 }, { row: 0, col: 1 }, false), true);
	assert.equal(isAdjacent({ row: 0, col: 0 }, { row: 1, col: 1 }, false), false);
	assert.equal(isAdjacent({ row: 0, col: 0 }, { row: 1, col: 1 }, true), true);
	assert.equal(isAdjacent({ row: 0, col: 0 }, { row: 0, col: 0 }, true), false);
	assert.equal(isAdjacent({ row: 0, col: 0 }, { row: 0, col: 2 }, true), false);
});

test('sameRegion lee la región del caso', () => {
	assert.equal(sameRegion(study, { row: 0, col: 0 }, { row: 0, col: 1 }), true);
	assert.equal(sameRegion(study, { row: 0, col: 0 }, { row: 1, col: 3 }), false);
});

test('holds evalúa todas las pistas contra la solución', () => {
	const expectations: [Clue, boolean][] = [
		[{ type: 'region', who: 's2', region: 1 }, true],
		[{ type: 'region', who: 's2', region: 0 }, false],
		[{ type: 'notRegion', who: 's1', region: 1 }, true],
		[{ type: 'notRegion', who: 's1', region: 0 }, false],
		[{ type: 'direction', who: 's3', dir: 'S', steps: 1, than: 's4' }, true],
		[{ type: 'direction', who: 's3', dir: 'N', steps: 1, than: 's4' }, false],
		[{ type: 'nearProp', who: 's1', prop: 'piano' }, true],
		[{ type: 'nearProp', who: 's2', prop: 'piano' }, false],
		[{ type: 'rowEdge', who: 's1', edge: 'top' }, true],
		[{ type: 'rowEdge', who: 's1', edge: 'bottom' }, false],
		[{ type: 'colEdge', who: 's2', edge: 'right' }, true],
		[{ type: 'colEdge', who: 's2', edge: 'left' }, false]
	];

	for (const [clue, expected] of expectations) {
		assert.equal(holds(clue, solution, study), expected, JSON.stringify(clue));
	}
});

test('holds resuelve adyacencia y regiones compartidas con una asignación armada', () => {
	const pair = { ...solution, s2: { row: 0, col: 1 } };

	assert.equal(holds({ type: 'adjacent', a: 's1', b: 's2', diagonal: false }, pair, study), true);
	assert.equal(holds({ type: 'sameRegion', a: 's1', b: 's2' }, pair, study), true);
	assert.equal(holds({ type: 'notSameRegion', a: 's1', b: 's2' }, pair, study), false);

	const diagonal = { ...solution, s2: { row: 1, col: 1 } };
	assert.equal(holds({ type: 'adjacent', a: 's1', b: 's2', diagonal: true }, diagonal, study), true);
	assert.equal(
		holds({ type: 'adjacent', a: 's1', b: 's2', diagonal: false }, diagonal, study),
		false
	);
});

test('canHold deja pasar lo desconocido y corta lo imposible', () => {
	assert.equal(canHold({ type: 'rowEdge', who: 's1', edge: 'top' }, {}, study), true);
	assert.equal(canHold({ type: 'rowEdge', who: 's1', edge: 'top' }, { s1: { row: 1, col: 0 } }, study), false);
	assert.equal(canHold({ type: 'rowEdge', who: 's1', edge: 'top' }, { s1: { row: 0, col: 0 } }, study), true);
	assert.equal(canHold({ type: 'direction', who: 's1', dir: 'S', steps: 1, than: 's2' }, {}, study), true);
});

test('killerOf exige un único sospechoso en la región de la víctima', () => {
	assert.equal(killerOf(study, solution), 's3');

	const withoutKiller = { ...solution };
	delete withoutKiller.s3;
	assert.equal(killerOf(study, withoutKiller), null);

	assert.equal(killerOf(study, { ...solution, s1: { row: 3, col: 0 } }), null);
});

test('isValidPlacement descarta filas, columnas, la víctima y el borde', () => {
	const fixed = { s2: { row: 1, col: 4 } };

	assert.equal(isValidPlacement(study, fixed, 's1', { row: 3, col: 3 }), true);
	assert.equal(isValidPlacement(study, fixed, 's1', { row: 1, col: 0 }), false);
	assert.equal(isValidPlacement(study, fixed, 's1', { row: 3, col: 4 }), false);
	assert.equal(isValidPlacement(study, fixed, 's1', { row: 2, col: 0 }), false);
	assert.equal(isValidPlacement(study, fixed, 's1', { row: 0, col: 2 }), false);
	assert.equal(isValidPlacement(study, fixed, 's1', { row: 5, col: 0 }), false);
	assert.equal(
		isValidPlacement(study, { s1: { row: 0, col: 0 } }, 's1', { row: 0, col: 1 }),
		true
	);
});
