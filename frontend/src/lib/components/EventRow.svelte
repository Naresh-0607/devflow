<script lang="ts">
	import { eventBranch, eventTitle, relativeTime } from '#lib/format';
	import type { GitEvent } from '#lib/types';
	import Icon from './Icon.svelte';

	let { event, showProject = false }: { event: GitEvent; showProject?: boolean } = $props();

	const meta = $derived.by(() => {
		switch (event.event_type) {
			case 'commit':
				return { icon: 'commit', tone: 'text-mint-300 bg-mint-400/10 ring-mint-400/20' };
			case 'branch_change':
				return { icon: 'branch', tone: 'text-iris-300 bg-iris-400/10 ring-iris-400/20' };
			case 'push':
				return { icon: 'push', tone: 'text-sky-300 bg-sky-400/10 ring-sky-400/20' };
			case 'repository_created':
				return { icon: 'plus', tone: 'text-amber-300 bg-amber-400/10 ring-amber-400/20' };
			default:
				return { icon: 'code', tone: 'text-zinc-300 bg-white/5 ring-white/10' };
		}
	});

	const branch = $derived(eventBranch(event.payload));
</script>

<div class="relative flex gap-3.5 py-3">
	<div class="grid h-8 w-8 shrink-0 place-items-center rounded-lg ring-1 ring-inset {meta.tone}">
		<Icon name={meta.icon} size={15} />
	</div>
	<div class="min-w-0 flex-1">
		<div class="flex items-start justify-between gap-3">
			<p class="truncate text-sm font-medium text-zinc-200">{eventTitle(event.event_type, event.payload)}</p>
			<span class="shrink-0 text-[11px] text-zinc-500">{relativeTime(event.created_at)}</span>
		</div>
		<div class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-zinc-500">
			{#if showProject && event.project_name}
				<span class="text-zinc-400">{event.project_name}</span>
				<span>·</span>
			{/if}
			{#if branch}
				<span class="inline-flex items-center gap-1 font-mono text-[10px] text-zinc-400">
					<Icon name="branch" size={10} />{branch}
				</span>
				<span>·</span>
			{/if}
			<span class="font-mono text-[10px] text-zinc-600">{event.repository_name ?? 'repository'}</span>
		</div>
	</div>
</div>
