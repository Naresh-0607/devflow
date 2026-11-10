<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		subtitle,
		children
	}: { title: string; subtitle?: string; children?: Snippet } = $props();
</script>

<header class="flex flex-wrap items-end justify-between gap-4">
	<div class="min-w-0">
		<h1 class="text-3xl font-semibold tracking-tight text-text">{title}</h1>
		{#if subtitle}
			<p class="mt-1.5 text-sm text-muted">{subtitle}</p>
		{/if}
	</div>
	{#if children}
		<div class="flex shrink-0 flex-wrap items-center gap-2">
			{@render children()}
		</div>
	{/if}
</header>
