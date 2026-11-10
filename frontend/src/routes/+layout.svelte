<script lang="ts">
	import '../app.css';
	import { afterNavigate, beforeNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { wakeBackend } from '#lib/api';
	import { auth } from '#lib/auth.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Logo from '#lib/components/Logo.svelte';
	import ThemeToggle from '#lib/components/ThemeToggle.svelte';
	import { theme } from '#lib/theme.svelte';
	import { onMount } from 'svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	const authPage = $derived(
		page.url.pathname === '/login' || page.url.pathname === '/register'
	);
	const isChat = $derived(page.url.pathname.startsWith('/chat'));

	const navItems = [
		{ href: '/', label: 'Dashboard', short: 'Dashboard', icon: 'home' },
		{ href: '/projects', label: 'Projects', short: 'Projects', icon: 'folder' },
		{ href: '/chat', label: 'Ask DevFlow', short: 'Ask', icon: 'message' },
		{ href: '/settings', label: 'Settings', short: 'Settings', icon: 'settings' }
	];

	function isActive(href: string) {
		return href === '/' ? page.url.pathname === '/' : page.url.pathname.startsWith(href);
	}

	const initial = $derived(auth.user?.email?.[0]?.toUpperCase() ?? '?');

	let navigationStarted = 0;
	beforeNavigate(() => {
		navigationStarted = performance.now();
	});
	afterNavigate(() => {
		if (!navigationStarted) return;
		const duration = performance.now() - navigationStarted;
		navigationStarted = 0;
		console.debug(`[devflow] route ${page.url.pathname} settled in ${duration.toFixed(0)}ms`);
	});

	onMount(() => {
		theme.init();
		auth.init();
		// Wake a sleeping Render instance while the shell paints.
		wakeBackend();

		const onUnauthorized = () => {
			auth.user = null;
			goto('/login');
		};
		window.addEventListener('devflow:unauthorized', onUnauthorized);
		return () => window.removeEventListener('devflow:unauthorized', onUnauthorized);
	});

	$effect(() => {
		if (!auth.ready) return;
		if (!auth.isAuthenticated && !authPage) goto('/login');
		if (auth.isAuthenticated && authPage) goto('/');
	});
</script>

<svelte:head>
	<title>DevFlow — Developer Memory</title>
</svelte:head>

{#if authPage}
	{@render children()}
{:else if !auth.ready}
	<div class="grid min-h-dvh place-items-center">
		<div class="flex items-center gap-3 text-sm text-zinc-500">
			<span class="h-4 w-4 animate-spin rounded-full border-2 border-white/15 border-t-mint-400"></span>
			Opening your memory…
		</div>
	</div>
{:else}
	<div class="flex min-h-dvh flex-col bg-ink-950">
		<!-- ambient glow -->
		<div class="pointer-events-none fixed inset-x-0 top-0 z-0 h-72 bg-[radial-gradient(60%_100%_at_50%_0%,rgba(79,224,173,0.07),transparent_70%)]"></div>

		<!-- Desktop sidebar -->
		<aside
			class="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-white/6 bg-ink-900/70 px-4 py-5 backdrop-blur-xl md:flex"
		>
			<div class="px-2"><Logo /></div>

			<nav class="mt-8 flex flex-col gap-1" aria-label="Primary">
				{#each navItems as item}
					<a
						href={item.href}
						data-sveltekit-preload-data="hover"
						aria-current={isActive(item.href) ? 'page' : undefined}
						class="flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition {isActive(item.href)
							? 'bg-white/8 text-zinc-50'
							: 'text-zinc-500 hover:bg-white/5 hover:text-zinc-200'}"
					>
						<Icon name={item.icon} size={17} class={isActive(item.href) ? 'text-mint-300' : ''} />
						{item.label}
						{#if isActive(item.href)}
							<span class="ml-auto h-1.5 w-1.5 rounded-full bg-mint-400"></span>
						{/if}
					</a>
				{/each}
			</nav>

			<div class="mt-auto space-y-3">
				<ThemeToggle />
				<div class="rounded-xl border border-white/6 bg-ink-850 p-3">
					<p class="text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Agent status</p>
					<p class="mt-1.5 flex items-center gap-1.5 text-xs text-zinc-400">
						<span class="h-1.5 w-1.5 rounded-full bg-mint-400 shadow-[0_0_8px_rgba(79,224,173,0.8)]"></span>
						Ready to remember
					</p>
				</div>
				<div class="flex items-center gap-2.5 rounded-xl px-2 py-1.5">
					<div class="grid h-8 w-8 place-items-center rounded-full bg-iris-500/20 text-xs font-semibold text-iris-200 ring-1 ring-inset ring-iris-400/30">
						{initial}
					</div>
					<div class="min-w-0 flex-1">
						<p class="truncate text-xs font-medium text-zinc-300">{auth.user?.email}</p>
						<p class="text-[10px] text-zinc-600">Developer</p>
					</div>
					<button
						onclick={() => auth.logout()}
						class="grid h-11 w-11 place-items-center rounded-xl text-zinc-600 transition hover:bg-white/5 hover:text-zinc-300"
						aria-label="Log out"
					>
						<Icon name="logout" size={15} />
					</button>
				</div>
			</div>
		</aside>

		<!-- Mobile header -->
		<header
			class="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-white/6 bg-ink-950/80 px-3 backdrop-blur-xl md:hidden"
		>
			<Logo size={28} />
			<div class="flex items-center gap-1">
				<ThemeToggle compact />
				<a
					href="/settings"
					class="grid h-11 w-11 place-items-center rounded-full"
					aria-label="Account settings"
				>
					<span class="grid h-8 w-8 place-items-center rounded-full bg-iris-500/20 text-xs font-semibold text-iris-200 ring-1 ring-inset ring-iris-400/30">
						{initial}
					</span>
				</a>
			</div>
		</header>

		<main
			class={isChat
				? 'relative z-10 flex min-h-0 flex-1 flex-col px-3 pb-20 pt-3 sm:px-6 md:ml-60 md:px-8 md:pb-8 md:pt-6'
				: 'relative z-10 px-4 pb-28 pt-6 sm:px-6 md:ml-60 md:px-8 md:pb-12 md:pt-8'}
		>
			{#if isChat}
				<div class="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
					{@render children()}
				</div>
			{:else}
				<div class="mx-auto w-full max-w-5xl animate-fade-up">
					{@render children()}
				</div>
			{/if}
		</main>

		<!-- Mobile bottom nav -->
		<nav
			class="fixed inset-x-0 bottom-0 z-30 border-t border-white/8 bg-ink-900/90 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl md:hidden"
			aria-label="Primary"
		>
			<div class="grid grid-cols-4">
				{#each navItems as item}
					<a
						href={item.href}
						data-sveltekit-preload-data="hover"
						aria-current={isActive(item.href) ? 'page' : undefined}
						class="flex min-h-14 flex-col items-center justify-center gap-1 py-2 text-[10px] font-medium transition {isActive(item.href)
							? 'text-mint-300'
							: 'text-zinc-500'}"
					>
						<Icon name={item.icon} size={19} />
						{item.short}
					</a>
				{/each}
			</div>
		</nav>
	</div>
{/if}
