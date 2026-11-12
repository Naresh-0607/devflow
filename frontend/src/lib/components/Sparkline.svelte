<script lang="ts">
	let {
		values,
		label = 'Recent activity'
	}: { values: number[]; label?: string } = $props();

	const peak = $derived(Math.max(1, ...values));
</script>

<div
	class="flex h-7 items-end gap-[3px]"
	role="img"
	aria-label="{label}: {values.reduce((sum, value) => sum + value, 0)} events over the last {values.length} days"
>
	{#each values as value, index}
		<span
			class="w-1 rounded-full bg-muted"
			style="height: {Math.max(2, Math.round((value / peak) * 28))}px; opacity: {value ? 0.85 : 0.2}"
		></span>
	{/each}
</div>
