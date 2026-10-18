import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	/** Base HTTP del backend; el default es el puerto que documenta `docs/api.md`. */
	PUBLIC_API_URL: {
		public: true,
		schema: (value) => value ?? 'http://localhost:8000'
	}
});
