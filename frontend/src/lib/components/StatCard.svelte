<script lang="ts">
	let {
		label,
		value,
		hint
	}: { label: string; value: string | number; hint?: string; icon?: string; tone?: string } = $props();
</script>

<div class="min-w-0 px-4 py-4 sm:px-5">
	<p class="text-xs text-muted">{label}</p>
	<p class="stat-value mt-1.5">{value}</p>
	{#if hint}
		<p class="mt-0.5 truncate text-xs text-muted">{hint}</p>
	{/if}
</div>
