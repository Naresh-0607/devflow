<script lang="ts">
	import { theme, type ThemeMode } from '#lib/theme.svelte';
	import Icon from './Icon.svelte';

	const modes: Array<{ id: ThemeMode; label: string; icon: string }> = [
		{ id: 'system', label: 'System', icon: 'monitor' },
		{ id: 'light', label: 'Light', icon: 'sun' },
		{ id: 'dark', label: 'Dark', icon: 'moon' }
	];
</script>

<div
	class="inline-flex rounded-control border border-border bg-bg p-0.5"
	role="group"
	aria-label="Appearance"
>
	{#each modes as mode}
		<button
			type="button"
			class="inline-flex min-h-11 items-center justify-center gap-1.5 rounded-[6px] px-3 text-xs font-medium transition {theme.mode ===
			mode.id
				? 'bg-surface text-text shadow-card'
				: 'text-muted hover:text-text'}"
			aria-pressed={theme.mode === mode.id}
			onclick={() => theme.set(mode.id)}
		>
			<Icon name={mode.icon} size={14} />
			{mode.label}
		</button>
	{/each}
</div>
