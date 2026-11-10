<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	let {
		icon = 'folder',
		title,
		description,
		children
	}: { icon?: string; title: string; description: string; children?: Snippet } = $props();
</script>

<div class="card flex flex-col items-center px-6 py-14 text-center">
	<span class="grid h-11 w-11 place-items-center rounded-control border border-border bg-raised text-muted">
		<Icon name={icon} size={20} />
	</span>
	<h2 class="mt-4 text-base font-semibold text-text">{title}</h2>
	<p class="mt-1.5 max-w-sm text-sm leading-relaxed text-muted">{description}</p>
	{#if children}
		<div class="mt-5 flex flex-wrap justify-center gap-2">
			{@render children()}
		</div>
	{/if}
</div>
