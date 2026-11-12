<script lang="ts">
	import '../app.css';
	import { afterNavigate, beforeNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { wakeBackend } from '#lib/api';
	import { auth } from '#lib/auth.svelte';
	import Icon from '#lib/components/Icon.svelte';
	import Logo from '#lib/components/Logo.svelte';
	import Toaster from '#lib/components/Toaster.svelte';
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
	let contentEl = $state<HTMLElement>();

	beforeNavigate(() => {
		navigationStarted = performance.now();
	});
	afterNavigate(() => {
		if (navigationStarted) {
			const duration = performance.now() - navigationStarted;
			navigationStarted = 0;
			console.debug(`[devflow] route ${page.url.pathname} settled in ${duration.toFixed(0)}ms`);
		}

		// Replay the subtle route transition on each navigation.
		if (!contentEl) return;
		contentEl.classList.remove('page-enter');
		void contentEl.offsetWidth;
		contentEl.classList.add('page-enter');
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
	<title>DevFlow</title>
</svelte:head>

{#if authPage}
	{@render children()}
{:else if !auth.ready}
	<div class="grid min-h-dvh place-items-center bg-bg">
		<div class="flex items-center gap-3 text-sm text-muted">
			<span class="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-text"></span>
			Loading…
		</div>
	</div>
{:else}
	<div class="flex min-h-dvh flex-col bg-bg">
		<!-- Desktop sidebar -->
		<aside
			class="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-surface px-3 py-5 lg:flex"
		>
			<div class="px-2"><Logo size={30} /></div>

			<nav class="mt-8 flex flex-col gap-1" aria-label="Primary">
				{#each navItems as item}
					<a
						href={item.href}
						data-sveltekit-preload-data="hover"
						aria-current={isActive(item.href) ? 'page' : undefined}
						class="flex min-h-11 items-center gap-3 rounded-control px-3 text-sm font-medium transition duration-150 {isActive(
							item.href
						)
							? 'bg-raised text-text'
							: 'text-muted hover:bg-raised/60 hover:text-text'}"
					>
						<Icon name={item.icon} size={17} />
						{item.label}
					</a>
				{/each}
			</nav>

			<div class="mt-auto border-t border-border pt-3">
				<div class="flex items-center gap-2.5 rounded-control px-2 py-2">
					<span
						class="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-border bg-raised text-xs font-semibold text-text"
					>
						{initial}
					</span>
					<div class="min-w-0 flex-1">
						<p class="truncate text-xs font-medium text-text">{auth.user?.email}</p>
						<p class="text-xs text-muted">Developer</p>
					</div>
					<button
						type="button"
						onclick={() => auth.logout()}
						class="btn-icon"
						aria-label="Log out"
					>
						<Icon name="logout" size={15} />
					</button>
				</div>
			</div>
		</aside>

		<div class="flex min-h-dvh flex-1 flex-col lg:pl-60">
			<!-- Mobile header -->
			<header
				class="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-bg/90 px-4 backdrop-blur-md lg:hidden"
			>
				<Logo size={28} />
				<a
					href="/settings"
					class="grid h-11 w-11 place-items-center rounded-control"
					aria-label="Account settings"
				>
					<span
						class="grid h-8 w-8 place-items-center rounded-full border border-border bg-raised text-xs font-semibold text-text"
					>
						{initial}
					</span>
				</a>
			</header>

			<main
				class={isChat
					? 'flex min-h-0 flex-1 flex-col px-3 pb-[calc(4.5rem+env(safe-area-inset-bottom))] pt-3 sm:px-6 lg:px-8 lg:pb-6 lg:pt-6'
					: 'flex-1 px-4 pb-28 pt-6 sm:px-6 lg:px-8 lg:pb-16 lg:pt-10'}
			>
				<div
					bind:this={contentEl}
					class={isChat
						? 'page-enter mx-auto flex h-full min-h-0 w-full max-w-3xl flex-1 flex-col'
						: 'page-enter mx-auto w-full max-w-[960px]'}
				>
					{@render children()}
				</div>
			</main>
		</div>

		<!-- Mobile bottom nav -->
		<nav
			class="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md lg:hidden"
			aria-label="Primary"
		>
			<div class="grid grid-cols-4">
				{#each navItems as item}
					<a
						href={item.href}
						data-sveltekit-preload-data="hover"
						aria-current={isActive(item.href) ? 'page' : undefined}
						class="relative flex min-h-14 flex-col items-center justify-center gap-1 py-2 text-[11px] font-medium transition {isActive(
							item.href
						)
							? 'text-text'
							: 'text-muted'}"
					>
						{#if isActive(item.href)}
							<span
								class="absolute inset-x-0 top-0 mx-auto h-0.5 w-8 rounded-full bg-text"
								aria-hidden="true"
							></span>
						{/if}
						<Icon name={item.icon} size={19} />
						{item.short}
					</a>
				{/each}
			</div>
		</nav>

		<Toaster />
	</div>
{/if}
