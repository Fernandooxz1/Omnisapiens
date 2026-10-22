import assert from 'node:assert/strict';
import test from 'node:test';
import { fixtureCases } from './fixtures.ts';
import type { MurdokuCase } from './types.ts';
import { validateCase, validateCatalog } from './validate.ts';

const [study, library] = fixtureCases;

test('los casos de fixture son publicables', () => {
	assert.deepEqual(validateCase(study), []);
	assert.deepEqual(validateCase(library), []);
});

test('detecta una pista falsa', () => {
	const broken: MurdokuCase = structuredClone(study);
	broken.suspects[0].clues = [{ type: 'nearProp', who: 's1', prop: 'planta' }];

	const errors = validateCase(broken);
	assert.equal(errors.length, 1);
	assert.match(errors[0], /no se cumple en la solución/);
});

test('detecta un asesino incorrecto', () => {
	const broken: MurdokuCase = structuredClone(study);
	broken.killer = 's1';

	const errors = validateCase(broken);
	assert.ok(errors.some((error) => error.includes('El asesino declarado')));
});

test('detecta iniciales repetidas', () => {
	const broken: MurdokuCase = structuredClone(study);
	broken.suspects[1].initial = 'B';

	const errors = validateCase(broken);
	assert.ok(errors.some((error) => error.includes('La inicial "B" se repite')));
});

test('detecta un caso con más de una solución', () => {
	const broken: MurdokuCase = structuredClone(library);
	broken.suspects[7].clues = [{ type: 'rowEdge', who: 's8', edge: 'bottom' }];

	const errors = validateCase(broken);
	assert.ok(errors.some((error) => error.includes('más de una solución')));
});

test('validateCatalog detecta ids, títulos y números repetidos', () => {
	const clone: MurdokuCase = structuredClone(study);
	const errors = validateCatalog([study, clone]);

	assert.ok(errors.some((error) => error.includes('id duplicado')));
	assert.ok(errors.some((error) => error.includes('título duplicado')));
	assert.ok(errors.some((error) => error.includes('número de caso duplicado')));
});
