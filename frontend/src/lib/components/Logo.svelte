<script lang="ts">
	let { size = 34, withWordmark = true }: { size?: number; withWordmark?: boolean } = $props();
</script>

<a href="/" class="flex items-center gap-2.5" aria-label="DevFlow home">
	<span
		class="relative grid place-items-center rounded-[10px] bg-gradient-to-br from-mint-400 to-iris-400 shadow-[0_0_24px_-6px_rgba(79,224,173,0.5)]"
		style="width: {size}px; height: {size}px"
	>
		<svg viewBox="0 0 24 24" width={size * 0.62} height={size * 0.62} fill="none">
			<path d="M6 4v16" stroke="#07080c" stroke-width="2.4" stroke-linecap="round" opacity="0.55" />
			<circle cx="6" cy="4" r="1.6" fill="#07080c" />
			<circle cx="6" cy="12" r="1.6" fill="#07080c" opacity="0.7" />
			<circle cx="6" cy="20" r="1.6" fill="#07080c" />
			<path d="M10 4h4.5c3.3 0 5.5 2.2 5.5 5.5v2c0 3.6-2.6 6.5-6.2 6.5H11" stroke="#07080c" stroke-width="2.4" stroke-linecap="round" />
		</svg>
	</span>
	{#if withWordmark}
		<span class="text-[17px] font-semibold tracking-tight text-zinc-50">
			Dev<span class="text-mint-300">Flow</span>
		</span>
	{/if}
</a>
