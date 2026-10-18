<script lang="ts">
	import { goto } from '$app/navigation';
	import AccentPicker from '#lib/components/AccentPicker.svelte';
	import Avatar from '#lib/components/Avatar.svelte';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import NickInput from '#lib/components/NickInput.svelte';
	import { t } from '#lib/i18n';

	let nick = $state('');
	const nickReady = $derived(nick.trim().length > 0);
	/** El arcade da tres vidas: se muestran como pastilla del modo. */
	const lives = [1, 2, 3];
</script>

<div class="home">
	<div class="home__main">
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
				bind:value={nick}
			>
				{#snippet prefix()}
					<Avatar {nick} />
				{/snippet}
			</NickInput>
			<AccentPicker label={t('home.accent_label')} />
		</div>

		<nav class="modes" aria-label={t('home.modes')}>
			<Button
				variant="green"
				title={t('home.play_arcade')}
				sub={t('home.play_arcade_hint')}
				onclick={() => goto('/arcade')}
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
				onclick={() => goto('/play')}
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
		display: flex;
		flex-direction: column;
		gap: var(--s-5);
	}
</style>
