<script lang="ts">
	import { eventBranch, eventTitle, formatDateTime, relativeTime } from '#lib/format';
	import type { GitEvent } from '#lib/types';
	import Icon from './Icon.svelte';

	let {
		events,
		showProject = false,
		emptyText = 'No events yet. Install the agent to start the timeline.'
	}: { events: GitEvent[]; showProject?: boolean; emptyText?: string } = $props();

	const eventMeta: Record<string, { icon: string; tone: string }> = {
		commit: { icon: 'commit', tone: 'text-mint-300 bg-mint-400/10 ring-mint-400/25' },
		branch_change: { icon: 'branch', tone: 'text-iris-300 bg-iris-400/10 ring-iris-400/25' },
		push: { icon: 'push', tone: 'text-sky-300 bg-sky-400/10 ring-sky-400/25' },
		repository_created: { icon: 'plus', tone: 'text-amber-300 bg-amber-400/10 ring-amber-400/25' }
	};

	function dayLabel(date: Date): string {
		const today = new Date();
		const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
		const target = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
		const days = Math.round((midnight - target) / 86400000);
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		return date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'short' });
	}

	const groups = $derived.by(() => {
		const map = new Map<string, { label: string; events: GitEvent[] }>();
		for (const event of events) {
			const date = new Date(event.created_at);
			const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
			const group = map.get(key) ?? { label: dayLabel(date), events: [] };
			group.events.push(event);
			map.set(key, group);
		}
		return [...map.values()];
	});
</script>

{#if events.length === 0}
	<p class="py-8 text-center text-sm text-zinc-600">{emptyText}</p>
{:else}
	<div class="space-y-6">
		{#each groups as group}
			<section>
				<div class="mb-2 flex items-center gap-3">
					<h3 class="section-title">{group.label}</h3>
					<span class="h-px flex-1 bg-white/8"></span>
					<span class="text-[10px] font-medium text-zinc-600">{group.events.length}</span>
				</div>
				<ol>
					{#each group.events as event, index (event.id)}
						{@const meta = eventMeta[event.event_type] ?? {
							icon: 'code',
							tone: 'text-zinc-300 bg-white/5 ring-white/10'
						}}
						{@const branch = eventBranch(event.payload)}
						<li class="relative flex gap-3.5 pb-4 last:pb-0">
							{#if index < group.events.length - 1}
								<span class="absolute bottom-0 left-[15px] top-9 w-px bg-white/8" aria-hidden="true"></span>
							{/if}
							<span
								class="relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-lg ring-1 ring-inset {meta.tone}"
							>
								<Icon name={meta.icon} size={15} />
							</span>
							<div class="min-w-0 flex-1 pt-0.5">
								<div class="flex items-start justify-between gap-3">
									<p class="text-sm font-medium leading-snug text-zinc-200">
										{eventTitle(event.event_type, event.payload)}
									</p>
									<time
										class="shrink-0 text-[11px] text-zinc-500"
										datetime={event.created_at}
										title={formatDateTime(event.created_at)}
									>
										{relativeTime(event.created_at)}
									</time>
								</div>
								<div class="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-zinc-500">
									{#if showProject && event.project_name}
										<span class="font-medium text-zinc-400">{event.project_name}</span>
										<span aria-hidden="true">·</span>
									{/if}
									{#if branch}
										<span class="inline-flex items-center gap-1 font-mono text-[10px] text-zinc-400">
											<Icon name="branch" size={10} />{branch}
										</span>
										<span aria-hidden="true">·</span>
									{/if}
									<span class="truncate font-mono text-[10px] text-zinc-600">
										{event.repository_name ?? 'repository'}
									</span>
								</div>
							</div>
						</li>
					{/each}
				</ol>
			</section>
		{/each}
	</div>
{/if}
