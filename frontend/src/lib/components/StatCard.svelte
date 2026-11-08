<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		label,
		value,
		icon,
		hint,
		tone = 'text-mint-300'
	}: { label: string; value: string | number; icon: string; hint?: string; tone?: string } = $props();
</script>

<div class="panel p-4 sm:p-5">
	<div class="flex items-center justify-between">
		<span class="section-title">{label}</span>
		<Icon name={icon} size={15} class={tone} />
	</div>
	<p class="stat-value mt-3">{value}</p>
	{#if hint}
		<p class="mt-1 text-xs text-zinc-500">{hint}</p>
	{/if}
</div>
