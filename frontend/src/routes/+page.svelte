<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { ApiError, NETWORK_ERROR } from '#lib/api/client';
	import { fetchModes, type GameMode } from '#lib/api/modes';
	import { session } from '#lib/api/session.svelte';
	import AccentPicker from '#lib/components/AccentPicker.svelte';
	import Avatar from '#lib/components/Avatar.svelte';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import NickInput from '#lib/components/NickInput.svelte';
	import SoundToggle from '#lib/components/SoundToggle.svelte';
	import { t, type MessageKey } from '#lib/i18n';
	import { modeEntry, orderModes } from '#lib/modes/registry';
	import { toast } from '#lib/toast.svelte';

	/** Falla del campo: se marca el pozo del nick en vez de avisar suelto. */
	const FIELD_ERRORS: MessageKey[] = ['home.nick_taken', 'home.nick_invalid'];

	let nick = $state('');
	let entering = $state(false);
	let error = $state<MessageKey | null>(null);
	let modes = $state<GameMode[]>([]);
	let modesLoading = $state(true);
	let modesFailed = $state(false);
	const nickReady = $derived(nick.trim().length > 0);
	const fieldError = $derived(error && FIELD_ERRORS.includes(error) ? t(error) : undefined);
	const catalog = $derived(orderModes(modes));
	/** Solo los modos que publican tabla muestran el acceso al ranking. */
	const showRanking = $derived(modes.some((mode) => mode.ranking));
	/** El arcade da tres vidas: se muestran como pastilla del modo. */
	const lives = [1, 2, 3];

	onMount(async () => {
		void loadModes();
		await session.restore();
		if (!nick && session.user) nick = session.user.nick;
	});

	async function loadModes() {
		modesLoading = true;
		try {
			modes = await fetchModes();
			modesFailed = false;
		} catch {
			modesFailed = true;
		} finally {
			modesLoading = false;
		}
	}

	/** El nick es obligatorio: la sesión se resuelve acá y recién después se entra. */
	async function enter(path: string) {
		if (entering) return;

		entering = true;
		error = null;

		try {
			await session.identify(nick);
			await goto(path);
		} catch (failure) {
			const key = errorKey(failure);
			error = key;
			if (key === 'home.enter_failed') toast.failure(failure, t(key));
		} finally {
			entering = false;
		}
	}

	function errorKey(failure: unknown): MessageKey {
		if (!(failure instanceof ApiError)) return 'home.enter_failed';

		switch (failure.code) {
			case NETWORK_ERROR:
				return 'home.enter_offline';
			case 'NICK_TAKEN':
				return 'home.nick_taken';
			case 'NICK_LENGTH':
			case 'NICK_FORBIDDEN':
				return 'home.nick_invalid';
			default:
				return 'home.enter_failed';
		}
	}
</script>

<div class="home">
	<div class="home__main">
		<div class="home__tools">
			<SoundToggle />
		</div>

		<header class="hero">
			<span class="wordmark-badge">{t('home.badge')}</span>
			<h1 class="wordmark">
				{t('home.wordmark_omni')}<span class="wordmark__accent">{t('home.wordmark_sapiens')}</span>
			</h1>
			<p class="tagline">{t('home.tagline')}</p>
		</header>

		<div class="profile">
			<NickInput
				id="nick"
				label={t('home.nick_label')}
				hint={t('home.nick_hint')}
				valid={nickReady}
				error={fieldError}
				bind:value={nick}
			>
				{#snippet prefix()}
					<Avatar {nick} />
				{/snippet}
			</NickInput>
			<AccentPicker label={t('home.accent_label')} />
		</div>

		{#if error && !fieldError}
			<p class="home__error" role="alert">{t(error)}</p>
		{/if}

		{#if modesLoading && catalog.length === 0}
			<div class="modes" aria-hidden="true">
				<span class="mode-skeleton"></span>
				<span class="mode-skeleton"></span>
			</div>
		{:else if modesFailed}
			<div class="error-block">
				<p class="home__error" role="alert">{t('home.modes_error')}</p>
				<Button variant="slate" title={t('home.modes_retry')} onclick={() => loadModes()} />
			</div>
		{:else if catalog.length > 0}
			<nav class="modes" aria-label={t('home.modes')}>
				{#each catalog as mode (mode.code)}
					{@const entry = modeEntry(mode.code)}
					{#if entry}
						<Button
							variant={entry.variant}
							title={t(entry.title)}
							sub={t(entry.hint)}
							disabled={!nickReady || entering}
							onclick={() => enter(entry.route)}
						>
							{#snippet aside()}
								{#if entry.aside === 'lives'}
									<span class="pill">
										{#each lives as life (life)}
											<span class="pill__heart"><Icon name="heart" size={17} /></span>
										{/each}
									</span>
								{:else}
									<span class="pill pill--text">{t('home.vs')}</span>
								{/if}
							{/snippet}
						</Button>
					{:else}
						<Button variant="slate" title={mode.name} sub={t('home.mode_unavailable')} disabled />
					{/if}
				{/each}
			</nav>
		{/if}
	</div>

	{#if showRanking}
		<a class="rank-link" href="/ranking">
			<span class="rank-link__icon"><Icon name="trophy" /></span>
			{t('home.ranking')}
		</a>
	{/if}
</div>

<style>
	.home {
		display: flex;
		flex: 1;
		flex-direction: column;
		justify-content: space-between;
		gap: var(--s-6);
	}

	.home__main {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: var(--s-5);
	}

	.home__tools {
		position: absolute;
		top: 0;
		right: 0;
	}

	.home__error {
		margin-top: calc(-1 * var(--s-3));
		color: var(--red-ink);
		font-size: 0.875rem;
		font-weight: 600;
	}

	.error-block {
		display: flex;
		flex-direction: column;
		gap: var(--s-2);
	}

	.error-block .home__error {
		margin-top: 0;
	}

	.mode-skeleton {
		display: block;
		min-height: var(--key-h);
		border-radius: var(--r-key);
		background: var(--panel-bg);
		box-shadow: 0 5px 0 var(--panel-edge);
		opacity: 0.55;
	}
</style>
