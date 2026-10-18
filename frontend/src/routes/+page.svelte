<script lang="ts">
	import { goto } from '$app/navigation';
	import Button from '#lib/components/Button.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import NickInput from '#lib/components/NickInput.svelte';
	import SkinSwitcher from '#lib/components/SkinSwitcher.svelte';
	import { t } from '#lib/i18n';

	let nick = $state('');
	const nickReady = $derived(nick.trim().length > 0);
</script>

<div class="home">
	<div class="home__main">
		<header class="hero">
			<h1 class="wordmark">{t('app.title')}</h1>
			<p class="tagline">{t('home.tagline')}</p>
		</header>

		<NickInput
			id="nick"
			label={t('home.nick_label')}
			hint={t('home.nick_hint')}
			valid={nickReady}
			bind:value={nick}
		/>

		<nav class="modes" aria-label={t('home.modes')}>
			<Button
				variant="green"
				sheen
				title={t('home.play_arcade')}
				sub={t('home.play_arcade_hint')}
				onclick={() => goto('/arcade')}
			/>
			<Button
				variant="blue"
				title={t('home.play_online')}
				sub={t('home.play_online_hint')}
				onclick={() => goto('/play')}
			/>
		</nav>
	</div>

	<div class="home__foot">
		<SkinSwitcher groupLabel={t('home.style_group')} />
		<a class="rank-link" href="/ranking">
			<Icon name="trophy" />
			{t('home.ranking')}
			<Icon name="arrow" size={16} />
		</a>
	</div>
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

	.home__foot {
		display: flex;
		flex-direction: column;
		gap: var(--s-3);
	}
</style>
