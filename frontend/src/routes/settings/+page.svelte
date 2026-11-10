<script lang="ts">
	import { auth } from '#lib/auth.svelte';
	import { createDevice, fetchDevices, revokeDevice } from '#lib/api';
	import Icon from '#lib/components/Icon.svelte';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import ThemeToggle from '#lib/components/ThemeToggle.svelte';
	import { formatDate, relativeTime } from '#lib/format';
	import { toast } from '#lib/toast.svelte';
	import type { Device } from '#lib/types';
	import { onMount } from 'svelte';

	const endpoint = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	let devices = $state<Device[]>([]);
	let loading = $state(true);
	let error = $state('');

	let newName = $state('My laptop');
	let creating = $state(false);
	let createError = $state('');
	let createdKey = $state<string | null>(null);

	const commands = [
		{
			id: 'install',
			title: 'Install the agent',
			command: 'pip install -e path/to/devflow/agent'
		},
		{
			id: 'login',
			title: 'Connect this machine',
			command: `devflow login --key YOUR_KEY --endpoint ${endpoint}`
		},
		{
			id: 'hooks',
			title: 'Link a repository',
			command: 'cd your-repo && devflow install-hooks'
		}
	];

	async function load() {
		loading = true;
		error = '';
		try {
			devices = await fetchDevices();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not load devices';
		} finally {
			loading = false;
		}
	}

	async function addDevice() {
		if (!newName.trim()) return;
		creating = true;
		createError = '';
		try {
			const device = await createDevice(newName.trim());
			devices = [device, ...devices];
			createdKey = device.api_key;
			newName = 'My laptop';
			toast.show('API key created');
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Could not create a device';
		} finally {
			creating = false;
		}
	}

	async function revoke(device: Device) {
		if (!confirm(`Revoke "${device.name}"? Its agent will stop sending events.`)) return;
		try {
			await revokeDevice(device.id);
			devices = devices.filter((item) => item.id !== device.id);
			toast.show('Device revoked');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not revoke device';
		}
	}

	async function copy(text: string, label: string) {
		try {
			await navigator.clipboard.writeText(text);
			toast.show(`${label} copied`);
		} catch {
			toast.show('Could not copy to the clipboard', 'error');
		}
	}

	function isOnline(device: Device): boolean {
		if (!device.last_seen) return false;
		return Date.now() - new Date(device.last_seen).getTime() < 7 * 86400000;
	}

	onMount(load);
</script>

<svelte:head><title>Settings — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
	<PageHeader
		title="Settings"
		subtitle="Your account, connected machines and the way DevFlow looks."
	/>

	<!-- Account -->
	<section class="card p-6">
		<div class="flex items-center gap-2.5">
			<span class="grid h-8 w-8 place-items-center rounded-control border border-border bg-raised text-muted">
				<Icon name="user" size={15} />
			</span>
			<div>
				<h2 class="text-sm font-semibold text-text">Account</h2>
				<p class="text-xs text-muted">Your DevFlow identity</p>
			</div>
		</div>

		<div class="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-control border border-border bg-bg p-4">
			<div class="flex min-w-0 items-center gap-3">
				<span class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-raised text-sm font-semibold text-text">
					{auth.user?.email?.[0]?.toUpperCase() ?? '?'}
				</span>
				<div class="min-w-0">
					<p class="truncate text-sm font-medium text-text">{auth.user?.email}</p>
					<p class="text-xs text-muted">Member since {formatDate(auth.user?.created_at)}</p>
				</div>
			</div>
			<button class="btn-secondary" onclick={() => auth.logout()}>
				<Icon name="logout" size={14} /> Sign out
			</button>
		</div>

		<div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
			<div>
				<p class="text-sm font-medium text-text">Appearance</p>
				<p class="text-xs text-muted">Follow your system, or choose light or dark.</p>
			</div>
			<ThemeToggle />
		</div>
	</section>

	<!-- Devices & API keys -->
	<section class="card p-6">
		<div class="flex items-center gap-2.5">
			<span class="grid h-8 w-8 place-items-center rounded-control border border-border bg-raised text-muted">
				<Icon name="key" size={15} />
			</span>
			<div>
				<h2 class="text-sm font-semibold text-text">Devices &amp; API keys</h2>
				<p class="text-xs text-muted">API keys that can send Git events</p>
			</div>
		</div>

		<form
			class="mt-4 flex flex-col gap-2 sm:flex-row"
			onsubmit={(event) => {
				event.preventDefault();
				addDevice();
			}}
		>
			<label class="sr-only" for="device-name">Device name</label>
			<input
				id="device-name"
				class="input flex-1"
				placeholder="Device name (e.g. Work laptop)"
				bind:value={newName}
				maxlength="120"
			/>
			<button type="submit" class="btn-primary shrink-0" disabled={creating}>
				<Icon name="plus" size={15} /> {creating ? 'Generating…' : 'Generate API key'}
			</button>
		</form>
		{#if createError}<p class="mt-2 text-xs text-danger">{createError}</p>{/if}

		{#if createdKey}
			<div class="mt-4 rounded-control border border-accent/30 bg-accent-soft p-4">
				<p class="text-xs font-semibold text-accent">Your new API key — shown only once</p>
				<div class="mt-2 flex items-center gap-2">
					<code
						class="min-w-0 flex-1 overflow-x-auto whitespace-nowrap rounded-control border border-border bg-bg px-3 py-2 font-mono text-xs text-text"
					>
						{createdKey}
					</code>
					<button
						class="btn-secondary shrink-0 px-3 py-2 text-xs"
						onclick={() => copy(createdKey!, 'API key')}
					>
						<Icon name="copy" size={14} /> Copy
					</button>
				</div>
				<p class="mt-2 text-xs text-muted">
					Paste it into <code class="font-mono text-text">devflow login --key …</code>. Store it
					somewhere safe.
				</p>
				<button
					class="mt-2 min-h-11 text-xs text-muted underline underline-offset-2 hover:text-text"
					onclick={() => (createdKey = null)}
				>
					I've saved it
				</button>
			</div>
		{/if}

		<div class="mt-5">
			{#if loading}
				<div class="space-y-2">
					{#each Array(2) as _}<div class="skeleton h-16 w-full"></div>{/each}
				</div>
			{:else if error}
				<p class="text-xs text-danger">{error}</p>
			{:else if devices.length === 0}
				<div class="rounded-control border border-dashed border-border px-4 py-8 text-center">
					<p class="text-sm text-muted">No devices connected yet.</p>
					<p class="mt-1 text-xs text-muted">Generate a key above to connect your first machine.</p>
				</div>
			{:else}
				<div class="divide-y divide-border">
					{#each devices as device (device.id)}
						<div class="flex items-center justify-between gap-3 py-3">
							<div class="flex min-w-0 items-center gap-3">
								<span class="grid h-9 w-9 shrink-0 place-items-center rounded-control border border-border bg-raised text-muted">
									<Icon name="hard-drive" size={15} />
								</span>
								<div class="min-w-0">
									<p class="truncate text-sm font-medium text-text">{device.name}</p>
									<p class="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted">
										<span class="font-mono text-[11px]">{device.api_key_prefix}•••</span>
										<span aria-hidden="true">·</span>
										<span class="inline-flex items-center gap-1.5">
											<span
												class="h-1.5 w-1.5 rounded-full {isOnline(device)
													? 'bg-success'
													: 'bg-border'}"
											></span>
											last seen {relativeTime(device.last_seen)}
										</span>
									</p>
								</div>
							</div>
							<button
								class="btn-icon hover:text-danger"
								onclick={() => revoke(device)}
								aria-label="Revoke {device.name}"
							>
								<Icon name="trash" size={15} />
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</section>

	<!-- CLI setup -->
	<section class="card p-6">
		<div class="flex items-center gap-2.5">
			<span class="grid h-8 w-8 place-items-center rounded-control border border-border bg-raised text-muted">
				<Icon name="terminal" size={15} />
			</span>
			<div>
				<h2 class="text-sm font-semibold text-text">CLI setup</h2>
				<p class="text-xs text-muted">Install once per machine, link each repository</p>
			</div>
		</div>

		<ol class="mt-5 space-y-4">
			{#each commands as item, index}
				<li class="flex gap-3">
					<span
						class="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-border bg-raised text-[11px] font-semibold text-muted"
					>
						{index + 1}
					</span>
					<div class="min-w-0 flex-1">
						<p class="text-sm font-medium text-text">{item.title}</p>
						<div
							class="mt-2 flex items-center gap-2 rounded-control border border-border bg-bg px-3 py-2"
						>
							<code class="flex-1 overflow-x-auto whitespace-nowrap font-mono text-[11px] text-muted">
								{item.command}
							</code>
							<button
								class="grid h-9 w-9 shrink-0 place-items-center rounded-control text-muted transition hover:bg-raised hover:text-text"
								onclick={() => copy(item.command, item.title)}
								aria-label="Copy {item.title} command"
							>
								<Icon name="copy" size={13} />
							</button>
						</div>
						{#if item.id === 'hooks'}
							<p class="mt-1.5 text-xs text-muted">
								DevFlow installs non-blocking post-commit, post-checkout and pre-push hooks.
							</p>
						{/if}
					</div>
				</li>
			{/each}
		</ol>

		<div class="mt-5 flex items-start gap-2 rounded-control border border-border bg-bg p-3 text-xs leading-relaxed text-muted">
			<Icon name="check" size={13} class="mt-0.5 shrink-0 text-success" />
			<span>
				The agent is event-driven: it wakes on Git events only. No polling, no keystroke
				tracking, no screen-time measurement.
			</span>
		</div>
	</section>
</div>
