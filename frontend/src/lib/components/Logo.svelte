<script lang="ts">
	let { size = 32, withWordmark = true }: { size?: number; withWordmark?: boolean } = $props();
</script>

<a href="/" class="inline-flex items-center gap-2.5" aria-label="DevFlow home">
	<span
		class="grid shrink-0 place-items-center rounded-[10px] border border-border bg-raised text-text"
		style="width: {size}px; height: {size}px"
	>
		<svg viewBox="0 0 24 24" width={size * 0.58} height={size * 0.58} fill="none" aria-hidden="true">
			<path d="M6 4v16" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity="0.5" />
			<circle cx="6" cy="4" r="1.5" fill="currentColor" />
			<circle cx="6" cy="12" r="1.5" fill="currentColor" opacity="0.7" />
			<circle cx="6" cy="20" r="1.5" fill="currentColor" />
			<path
				d="M10 4h4.5c3.3 0 5.5 2.2 5.5 5.5v2c0 3.6-2.6 6.5-6.2 6.5H11"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
			/>
		</svg>
	</span>
	{#if withWordmark}
		<span class="text-[17px] font-semibold tracking-tight text-text">DevFlow</span>
	{/if}
</a>
