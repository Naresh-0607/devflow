<script lang="ts">
	import { toast } from '#lib/toast.svelte';
	import Icon from './Icon.svelte';

	const toneClass: Record<string, string> = {
		success: 'border-success/30 text-success',
		error: 'border-danger/30 text-danger',
		info: 'border-border text-text'
	};
	const toneIcon: Record<string, string> = {
		success: 'check-circle',
		error: 'alert-circle',
		info: 'sparkles'
	};
</script>

<div
	class="pointer-events-none fixed inset-x-4 bottom-24 z-50 flex flex-col items-center gap-2 lg:bottom-8 lg:left-auto lg:right-8 lg:items-end"
	aria-live="polite"
	aria-atomic="false"
>
	{#each toast.items as item (item.id)}
		<div
			class="pointer-events-auto flex w-full max-w-sm items-center gap-2.5 rounded-control border bg-surface px-3.5 py-2.5 text-sm shadow-card {toneClass[
				item.tone
			]}"
			role="status"
		>
			<Icon name={toneIcon[item.tone]} size={16} class="shrink-0" />
			<span class="min-w-0 flex-1 text-text">{item.message}</span>
			<button
				type="button"
				class="text-muted transition hover:text-text"
				onclick={() => toast.dismiss(item.id)}
				aria-label="Dismiss notification"
			>
				<Icon name="x" size={14} />
			</button>
		</div>
	{/each}
</div>
