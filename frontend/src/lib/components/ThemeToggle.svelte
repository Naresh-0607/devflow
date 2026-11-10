<script lang="ts">
	import { theme } from '#lib/theme.svelte';
	import Icon from './Icon.svelte';

	let { compact = false }: { compact?: boolean } = $props();

	const label = $derived(
		theme.mode === 'system' ? 'System theme' : theme.mode === 'light' ? 'Light theme' : 'Dark theme'
	);
	const icon = $derived(theme.mode === 'system' ? 'monitor' : theme.mode === 'light' ? 'sun' : 'moon');
</script>

<button
	type="button"
	class={compact
		? 'grid h-11 w-11 place-items-center rounded-xl text-zinc-400 transition hover:bg-white/5 hover:text-zinc-100'
		: 'flex min-h-11 w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-500 transition hover:bg-white/5 hover:text-zinc-200'}
	onclick={() => theme.cycle()}
	aria-label="{label}. Tap to change theme."
	title={label}
>
	<Icon name={icon} size={compact ? 18 : 17} class={compact ? '' : 'text-iris-300'} />
	{#if !compact}<span>{label}</span>{/if}
</button>
