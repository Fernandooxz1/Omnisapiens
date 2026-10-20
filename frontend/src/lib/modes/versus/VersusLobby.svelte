<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError, NETWORK_ERROR } from '#lib/api/client';
	import { createRoom, previewRoom } from '#lib/api/rooms';
	import { session } from '#lib/api/session.svelte';
	import Button from '#lib/components/Button.svelte';
	import CodeInput from '#lib/components/CodeInput.svelte';
	import { t, type MessageKey } from '#lib/i18n';
	import { toast } from '#lib/toast.svelte';

	const ROUNDS = [3, 5, 7] as const;
	const SECONDS = [10, 20, 30] as const;
	const CODE = /^[A-Z2-9]{6}$/;

	let rounds = $state<number>(5);
	let seconds = $state<number>(20);
	let code = $state('');
	let busy = $state<'create' | 'join' | null>(null);
	let error = $state<MessageKey | null>(null);
	let blocked = $state<MessageKey | null>(null);

	const canJoin = $derived(CODE.test(code));

	onMount(() => {
		(async () => {
			await session.restore();

			if (!session.token) {
				blocked = 'play.error_auth';
				return;
			}

			// Enlace viejo: la sala ahora vive en su propia ruta.
			const legacy = page.url.searchParams.get('code');
			if (legacy) await goto(`/room/${legacy.toUpperCase()}`, { replaceState: true });
		})();
	});

	async function create() {
		if (!session.token || busy) return;

		busy = 'create';
		error = null;

		try {
			const room = await createRoom(session.token, { rounds, seconds });
			await goto(`/room/${room.code}`);
		} catch (failure) {
			const key = errorKey(failure);
			error = key;
			if (key === 'play.error_generic') toast.failure(failure, t(key));
		} finally {
			busy = null;
		}
	}

	async function join(submitted?: string) {
		const wanted = (submitted ?? code).toUpperCase();
		if (!session.token || busy || !CODE.test(wanted)) return;

		busy = 'join';
		error = null;

		try {
			const room = await previewRoom(wanted);

			if (room.status !== 'waiting') {
				error = 'play.error_started';
				return;
			}
			if (room.players >= 2) {
				error = 'play.error_full';
				return;
			}

			await goto(`/room/${room.code}`);
		} catch (failure) {
			const key = errorKey(failure);
			error = key;
			if (key === 'play.error_generic') toast.failure(failure, t(key));
		} finally {
			busy = null;
		}
	}

	function errorKey(failure: unknown): MessageKey {
		if (!(failure instanceof ApiError)) return 'play.error_generic';
		if (failure.code === NETWORK_ERROR) return 'play.error_offline';

		switch (failure.code) {
			case 'AUTH_REQUIRED':
				return 'play.error_auth';
			case 'ROOM_NOT_FOUND':
				return 'play.error_room';
			case 'ROOM_FULL':
				return 'play.error_full';
			case 'RATE_LIMITED':
				return 'play.error_limited';
			default:
				return 'play.error_generic';
		}
	}
</script>

{#if blocked}
	<section class="play">
		<div class="play__intro">
			<h1 class="page-title">{t('play.title')}</h1>
			<p class="muted">{t(blocked)}</p>
		</div>
		<a class="rank-link" href="/">{t('common.back')}</a>
	</section>
{:else}
	<section class="play">
		<header class="play__intro">
			<h1 class="page-title">{t('play.title')}</h1>
			<p class="muted">{t('play.subtitle')}</p>
		</header>

		{#if error}
			<p class="play__error" role="alert">{t(error)}</p>
		{/if}

		<div class="play__card">
			<h2 class="play__title">{t('play.create_title')}</h2>

			<div class="choice">
				<span class="choice__label">{t('play.rounds')}</span>
				<div class="segmented" role="group" aria-label={t('play.rounds')}>
					{#each ROUNDS as value (value)}
						<button
							type="button"
							class="segment"
							class:is-on={rounds === value}
							aria-pressed={rounds === value}
							onclick={() => (rounds = value)}
						>
							{t('play.rounds_value', { n: value })}
						</button>
					{/each}
				</div>
			</div>

			<div class="choice">
				<span class="choice__label">{t('play.seconds')}</span>
				<div class="segmented" role="group" aria-label={t('play.seconds')}>
					{#each SECONDS as value (value)}
						<button
							type="button"
							class="segment"
							class:is-on={seconds === value}
							aria-pressed={seconds === value}
							onclick={() => (seconds = value)}
						>
							{t('play.seconds_value', { n: value })}
						</button>
					{/each}
				</div>
			</div>

			<Button
				variant="green"
				title={busy === 'create' ? t('play.creating') : t('play.create')}
				disabled={busy !== null}
				onclick={() => create()}
			/>
		</div>

		<p class="play__or" aria-hidden="true">{t('play.or')}</p>

		<div class="play__card">
			<h2 class="play__title">{t('play.join_title')}</h2>

			<CodeInput label={t('play.code_label')} bind:value={code} oncomplete={(value) => join(value)} />

			<Button
				variant="blue"
				title={busy === 'join' ? t('play.joining') : t('play.join')}
				disabled={!canJoin || busy !== null}
				onclick={() => join()}
			/>
		</div>

		<a class="rank-link" href="/">{t('common.back')}</a>
	</section>
{/if}

<style>
	.play {
		display: flex;
		flex: 1;
		flex-direction: column;
		gap: var(--s-4);
	}

	.play__intro {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
		padding-top: var(--s-4);
	}

	.play__card {
		display: flex;
		flex-direction: column;
		gap: var(--s-4);
		padding: var(--s-4);
		border-radius: var(--r-lg);
		background: var(--panel-bg);
		box-shadow: 0 5px 0 var(--panel-edge);
	}

	.play__title {
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 1.2rem;
	}

	.play__or {
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		text-align: center;
	}

	.play__error {
		color: var(--red-ink);
		font-size: 0.9rem;
		font-weight: 600;
		text-align: center;
	}

	.choice {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.choice__label {
		color: var(--ink-3);
		font-size: 0.8125rem;
		font-weight: 600;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}

	.segmented {
		display: flex;
		gap: var(--s-1);
		padding: 4px;
		border-radius: var(--r-md);
		background: var(--well-bg);
		box-shadow: inset 0 3px 0 rgb(0 0 0 / 0.35);
	}

	.segment {
		flex: 1;
		min-height: 44px;
		padding: 0 var(--s-2);
		border: 0;
		border-radius: var(--r-sm);
		background: transparent;
		color: var(--ink-3);
		font-family: var(--font-display);
		font-size: 0.95rem;
		font-weight: 700;
		cursor: pointer;
	}

	.segment.is-on {
		background: var(--panel-bg);
		box-shadow: 0 3px 0 var(--panel-edge);
		color: var(--ink);
	}
</style>
