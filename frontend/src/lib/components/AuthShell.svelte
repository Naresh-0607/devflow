<script lang="ts">
	import Icon from './Icon.svelte';
	import Logo from './Logo.svelte';
	import type { Snippet } from 'svelte';

	let {
		title,
		subtitle,
		children
	}: { title: string; subtitle: string; children: Snippet } = $props();

	const points = [
		{ icon: 'commit', text: 'Captures commits automatically' },
		{ icon: 'branch', text: 'Tracks your focus across branches' },
		{ icon: 'activity', text: 'Generates a readable summary of your work' }
	];
</script>

<div class="grid min-h-dvh lg:grid-cols-2">
	<!-- Brand panel -->
	<div
		class="relative hidden flex-col justify-between border-r border-border bg-surface p-12 lg:flex"
	>
		<div><Logo size={32} /></div>

		<div class="max-w-md">
			<p class="eyebrow">Developer timeline</p>
			<h2 class="mt-4 text-3xl font-semibold leading-tight tracking-tight text-text">
				Your Git activity,<br />on the record.
			</h2>
			<p class="mt-4 text-sm leading-relaxed text-muted">
				Your commits, branches and pushes become a timeline you can read from anywhere, with
				summaries and answers built on top of it.
			</p>

			<div class="mt-10 space-y-3">
				{#each points as point}
					<div class="flex items-center gap-3">
						<span class="grid h-8 w-8 place-items-center rounded-control border border-border bg-bg text-muted">
							<Icon name={point.icon} size={14} />
						</span>
						<span class="text-sm text-muted">{point.text}</span>
					</div>
				{/each}
			</div>
		</div>

		<p class="text-xs text-muted">
			No keyboard tracking. No screen time. Only Git events.
		</p>
	</div>

	<!-- Form panel -->
	<div class="flex flex-col justify-center px-5 py-10 sm:px-10">
		<div class="mx-auto w-full max-w-sm">
			<div class="mb-8 lg:hidden"><Logo size={30} /></div>
			<h1 class="text-3xl font-semibold tracking-tight text-text">{title}</h1>
			<p class="mt-1.5 text-sm text-muted">{subtitle}</p>
			<div class="mt-8">{@render children()}</div>
		</div>
	</div>
</div>
