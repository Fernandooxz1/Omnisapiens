<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { ApiError, NETWORK_ERROR } from '#lib/api/client';
	import { session } from '#lib/api/session.svelte';
	import AccentPicker from '#lib/components/AccentPicker.svelte';
	import Avatar from '#lib/components/Avatar.svelte';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import NickInput from '#lib/components/NickInput.svelte';
	import SoundToggle from '#lib/components/SoundToggle.svelte';
	import { t, type MessageKey } from '#lib/i18n';

	/** Falla del campo: se marca el pozo del nick en vez de avisar suelto. */
	const FIELD_ERRORS: MessageKey[] = ['home.nick_taken', 'home.nick_invalid'];

	let nick = $state('');
	let entering = $state(false);
	let error = $state<MessageKey | null>(null);
	const nickReady = $derived(nick.trim().length > 0);
	const fieldError = $derived(error && FIELD_ERRORS.includes(error) ? t(error) : undefined);
	/** El arcade da tres vidas: se muestran como pastilla del modo. */
	const lives = [1, 2, 3];

	onMount(async () => {
		await session.restore();
		if (!nick && session.user) nick = session.user.nick;
	});

	/** El nick es obligatorio: la sesión se resuelve acá y recién después se entra. */
	async function enter(path: string) {
		if (entering) return;

		entering = true;
		error = null;

		try {
			await session.identify(nick);
			await goto(path);
		} catch (failure) {
			error = errorKey(failure);
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

		<nav class="modes" aria-label={t('home.modes')}>
			<Button
				variant="green"
				title={t('home.play_arcade')}
				sub={t('home.play_arcade_hint')}
				disabled={!nickReady || entering}
				onclick={() => enter('/arcade')}
			>
				{#snippet aside()}
					<span class="pill">
						{#each lives as life (life)}
							<span class="pill__heart"><Icon name="heart" size={17} /></span>
						{/each}
					</span>
				{/snippet}
			</Button>
			<Button
				variant="blue"
				title={t('home.play_online')}
				sub={t('home.play_online_hint')}
				disabled={!nickReady || entering}
				onclick={() => enter('/play')}
			>
				{#snippet aside()}
					<span class="pill pill--text">{t('home.vs')}</span>
				{/snippet}
			</Button>
		</nav>
	</div>

	<a class="rank-link" href="/ranking">
		<span class="rank-link__icon"><Icon name="trophy" /></span>
		{t('home.ranking')}
	</a>
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
</style>
