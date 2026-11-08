<script lang="ts">
	import { auth } from '#lib/auth.svelte';
	import { createDevice, fetchDevices, revokeDevice } from '#lib/api';
	import Icon from '#lib/components/Icon.svelte';
	import { formatDate, relativeTime } from '#lib/format';
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
	let copied = $state('');

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
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not revoke device';
		}
	}

	async function copy(text: string, label: string) {
		try {
			await navigator.clipboard.writeText(text);
			copied = label;
			setTimeout(() => (copied = ''), 1800);
		} catch {
			copied = '';
		}
	}

	onMount(load);
</script>

<svelte:head><title>Settings — DevFlow</title></svelte:head>

<div class="flex flex-col gap-6">
	<div>
		<p class="text-xs font-medium uppercase tracking-[0.2em] text-mint-400/80">Configuration</p>
		<h1 class="mt-1.5 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">Settings</h1>
		<p class="mt-1.5 text-sm text-zinc-500">Your account, connected devices and agent setup.</p>
	</div>

	<!-- Account -->
	<section class="panel p-5 sm:p-6">
		<div class="flex items-center gap-2.5">
			<span class="grid h-8 w-8 place-items-center rounded-lg bg-white/5 text-zinc-300 ring-1 ring-inset ring-white/10"><Icon name="user" size={16} /></span>
			<div>
				<p class="text-sm font-semibold text-zinc-100">Account</p>
				<p class="text-[11px] text-zinc-600">Your DevFlow identity</p>
			</div>
		</div>
		<div class="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-white/6 bg-ink-900/50 p-4">
			<div class="flex items-center gap-3">
				<div class="grid h-10 w-10 place-items-center rounded-full bg-iris-500/20 text-sm font-semibold text-iris-200 ring-1 ring-inset ring-iris-400/30">
					{auth.user?.email?.[0]?.toUpperCase() ?? '?'}
				</div>
				<div>
					<p class="text-sm font-medium text-zinc-200">{auth.user?.email}</p>
					<p class="text-[11px] text-zinc-600">Member since {formatDate(auth.user?.created_at)}</p>
				</div>
			</div>
			<button class="btn-secondary text-xs" onclick={() => auth.logout()}><Icon name="logout" size={14} /> Sign out</button>
		</div>
	</section>

	<!-- Devices -->
	<section class="panel p-5 sm:p-6">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="flex items-center gap-2.5">
				<span class="grid h-8 w-8 place-items-center rounded-lg bg-mint-400/10 text-mint-300 ring-1 ring-inset ring-mint-400/20"><Icon name="device" size={16} /></span>
				<div>
					<p class="text-sm font-semibold text-zinc-100">Connected devices</p>
					<p class="text-[11px] text-zinc-600">API keys that can send Git events</p>
				</div>
			</div>
		</div>

		<form class="mt-4 flex flex-col gap-2 sm:flex-row" onsubmit={(event) => { event.preventDefault(); addDevice(); }}>
			<input class="input flex-1" placeholder="Device name (e.g. Work laptop)" bind:value={newName} maxlength="120" />
			<button type="submit" class="btn-primary shrink-0" disabled={creating}>
				<Icon name="plus" size={15} /> {creating ? 'Generating…' : 'Generate API key'}
			</button>
		</form>
		{#if createError}<p class="mt-2 text-xs text-red-300">{createError}</p>{/if}

		{#if createdKey}
			<div class="mt-4 rounded-xl border border-mint-400/25 bg-mint-400/5 p-4">
				<p class="text-xs font-semibold text-mint-200">Your new API key — shown only once</p>
				<div class="mt-2 flex items-center gap-2">
					<code class="flex-1 overflow-x-auto whitespace-nowrap rounded-lg bg-ink-950/70 px-3 py-2 font-mono text-xs text-mint-200">{createdKey}</code>
					<button class="btn-secondary shrink-0 px-3 py-2 text-xs" onclick={() => copy(createdKey!, 'key')}>
						<Icon name={copied === 'key' ? 'check' : 'copy'} size={14} />
						{copied === 'key' ? 'Copied' : 'Copy'}
					</button>
				</div>
				<p class="mt-2 text-[11px] text-zinc-500">Paste it into <code class="font-mono text-zinc-400">devflow login --key …</code>. Store it somewhere safe.</p>
				<button class="mt-2 text-[11px] text-zinc-500 underline hover:text-zinc-300" onclick={() => (createdKey = null)}>I've saved it</button>
			</div>
		{/if}

		<div class="mt-4">
			{#if loading}
				<div class="space-y-2">{#each Array(2) as _}<div class="skeleton h-14 w-full"></div>{/each}</div>
			{:else if error}
				<p class="text-xs text-red-300">{error}</p>
			{:else if devices.length === 0}
				<p class="rounded-xl border border-dashed border-white/10 px-4 py-6 text-center text-sm text-zinc-600">No devices connected yet.</p>
			{:else}
				<div class="space-y-2">
					{#each devices as device (device.id)}
						<div class="flex items-center justify-between gap-3 rounded-xl border border-white/6 bg-ink-900/40 px-4 py-3">
							<div class="flex min-w-0 items-center gap-3">
								<Icon name="device" size={16} class="shrink-0 text-zinc-500" />
								<div class="min-w-0">
									<p class="truncate text-sm font-medium text-zinc-200">{device.name}</p>
									<p class="font-mono text-[10px] text-zinc-600">{device.api_key_prefix}••• · last seen {relativeTime(device.last_seen)}</p>
								</div>
							</div>
							<button class="rounded-lg p-2 text-zinc-600 transition hover:bg-white/5 hover:text-red-300" onclick={() => revoke(device)} aria-label="Revoke {device.name}">
								<Icon name="trash" size={15} />
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</section>

	<!-- Agent setup -->
	<section class="panel p-5 sm:p-6">
		<div class="flex items-center gap-2.5">
			<span class="grid h-8 w-8 place-items-center rounded-lg bg-iris-500/10 text-iris-300 ring-1 ring-inset ring-iris-400/20"><Icon name="code" size={16} /></span>
			<div>
				<p class="text-sm font-semibold text-zinc-100">Local agent setup</p>
				<p class="text-[11px] text-zinc-600">Install once per machine, link each repository</p>
			</div>
		</div>

		<ol class="mt-5 space-y-4">
			<li class="flex gap-3">
				<span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/5 text-[11px] font-semibold text-zinc-400">1</span>
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-zinc-200">Generate an API key above</p>
					<p class="mt-0.5 text-xs text-zinc-500">Each machine gets its own key so you can revoke it independently.</p>
				</div>
			</li>
			<li class="flex gap-3">
				<span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/5 text-[11px] font-semibold text-zinc-400">2</span>
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-zinc-200">Install and connect the agent</p>
					<div class="mt-2 space-y-2">
						<div class="flex items-center gap-2 rounded-lg border border-white/6 bg-ink-950/60 px-3 py-2">
							<code class="flex-1 overflow-x-auto whitespace-nowrap font-mono text-[11px] text-zinc-300">pip install -e path/to/devflow/agent</code>
							<button class="text-zinc-600 hover:text-zinc-300" onclick={() => copy('pip install -e path/to/devflow/agent', 'pip')} aria-label="Copy install command"><Icon name={copied === 'pip' ? 'check' : 'copy'} size={13} /></button>
						</div>
						<div class="flex items-center gap-2 rounded-lg border border-white/6 bg-ink-950/60 px-3 py-2">
							<code class="flex-1 overflow-x-auto whitespace-nowrap font-mono text-[11px] text-zinc-300">devflow login --key dvf_live_… --endpoint {endpoint}</code>
							<button class="text-zinc-600 hover:text-zinc-300" onclick={() => copy(`devflow login --key YOUR_KEY --endpoint ${endpoint}`, 'login')} aria-label="Copy login command"><Icon name={copied === 'login' ? 'check' : 'copy'} size={13} /></button>
						</div>
					</div>
				</div>
			</li>
			<li class="flex gap-3">
				<span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-white/5 text-[11px] font-semibold text-zinc-400">3</span>
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-zinc-200">Link a repository</p>
					<div class="mt-2 flex items-center gap-2 rounded-lg border border-white/6 bg-ink-950/60 px-3 py-2">
						<code class="flex-1 overflow-x-auto whitespace-nowrap font-mono text-[11px] text-zinc-300">cd your-repo && devflow install-hooks</code>
						<button class="text-zinc-600 hover:text-zinc-300" onclick={() => copy('cd your-repo && devflow install-hooks', 'hooks')} aria-label="Copy hook command"><Icon name={copied === 'hooks' ? 'check' : 'copy'} size={13} /></button>
					</div>
					<p class="mt-1.5 text-[11px] text-zinc-600">DevFlow installs non-blocking post-commit, post-checkout and pre-push hooks.</p>
				</div>
			</li>
		</ol>

		<div class="mt-5 rounded-xl border border-white/6 bg-ink-900/40 p-3.5 text-[11px] leading-relaxed text-zinc-500">
			<Icon name="check" size={12} class="mr-1 inline text-mint-400" />
			The agent is event-driven: it wakes on Git events only. No polling, no keystroke tracking, no screen-time measurement.
		</div>
	</section>
</div>
