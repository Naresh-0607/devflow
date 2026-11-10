<script lang="ts">
	import { streamChat } from '#lib/api';
	import Icon from '#lib/components/Icon.svelte';
	import Markdown from '#lib/components/Markdown.svelte';
	import type { ChatHistoryMessage } from '#lib/types';
	import { tick } from 'svelte';

	type RetryPayload = { message: string; history: ChatHistoryMessage[] };
	type Message = {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		streaming?: boolean;
		tool?: string;
		tools?: string[];
		error?: string;
		retry?: RetryPayload;
	};

	const STORAGE_KEY = 'dvf_chat_messages';

	const suggestions = [
		'What was I working on yesterday?',
		'When did Jarvis start?',
		'Summarize this week',
		'Which project is most active?'
	];

	const toolLabels: Record<string, string> = {
		list_projects: 'Checking your projects',
		get_project: 'Opening project details',
		get_timeline: 'Reading your timeline',
		search_events: 'Searching your commits',
		get_summaries: 'Looking up summaries',
		get_stats: 'Counting activity'
	};

	function newId(): string {
		try {
			return crypto.randomUUID();
		} catch {
			return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
		}
	}

	function loadStored(): Message[] {
		try {
			const raw = sessionStorage.getItem(STORAGE_KEY);
			if (!raw) return [];
			const parsed = JSON.parse(raw) as Message[];
			if (!Array.isArray(parsed)) return [];
			return parsed
				.filter((message) => message && (message.role === 'user' || message.role === 'assistant'))
				.map((message) => ({ ...message, streaming: false }));
		} catch {
			return [];
		}
	}

	let messages = $state<Message[]>(loadStored());
	let input = $state('');
	let sending = $state(false);
	let scroller = $state<HTMLDivElement>();
	let composer = $state<HTMLTextAreaElement>();

	function persist() {
		try {
			sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
		} catch {
			/* session storage may be unavailable */
		}
	}

	function historyFrom(list: Message[]): ChatHistoryMessage[] {
		return list
			.filter((message) => !message.error && message.content.trim())
			.slice(-12)
			.map((message) => ({ role: message.role, content: message.content }));
	}

	function update(id: string, patch: Partial<Message>) {
		messages = messages.map((message) => (message.id === id ? { ...message, ...patch } : message));
	}

	async function requestAnswer(
		message: string,
		history: ChatHistoryMessage[],
		assistantId: string
	) {
		let accumulated = '';
		sending = true;

		try {
			await streamChat(
				{ message, history },
				{
					onToken: (chunk) => {
						accumulated += chunk;
						update(assistantId, { content: accumulated });
					},
					onTool: (name) => update(assistantId, { tool: name }),
					onDone: (answer, tools) => {
						update(assistantId, {
							content: answer || accumulated,
							streaming: false,
							tool: undefined,
							tools,
							error: undefined
						});
						persist();
					}
				}
			);
		} catch (error) {
			const detail =
				error instanceof Error ? error.message : 'DevFlow could not answer that question.';
			update(assistantId, {
				streaming: false,
				tool: undefined,
				error: detail,
				retry: { message, history }
			});
		} finally {
			sending = false;
			persist();
		}
	}

	async function submit(text = input) {
		const message = text.trim();
		if (!message || sending) return;

		const history = historyFrom(messages);
		const assistantId = newId();

		messages = [
			...messages,
			{ id: newId(), role: 'user', content: message },
			{ id: assistantId, role: 'assistant', content: '', streaming: true }
		];
		input = '';
		persist();
		await tick();
		composer?.focus();

		await requestAnswer(message, history, assistantId);
	}

	async function retry(message: Message) {
		if (sending || !message.retry) return;
		const retryPayload = message.retry;
		const assistantId = newId();

		messages = [
			...messages.filter((item) => item.id !== message.id),
			{ id: assistantId, role: 'assistant', content: '', streaming: true }
		];
		persist();
		await tick();
		await requestAnswer(retryPayload.message, retryPayload.history, assistantId);
	}

	function newChat() {
		messages = [];
		input = '';
		try {
			sessionStorage.removeItem(STORAGE_KEY);
		} catch {
			/* ignore */
		}
		composer?.focus();
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
			event.preventDefault();
			submit();
		}
	}

	$effect(() => {
		const stamp = `${messages.length}:${messages.at(-1)?.content.length ?? 0}:${sending}`;
		if (stamp && scroller) scroller.scrollTop = scroller.scrollHeight;
	});
</script>

<svelte:head><title>Ask DevFlow</title></svelte:head>

<div class="flex h-full min-h-0 flex-col">
	<header class="flex flex-none items-start justify-between gap-3 pb-3">
		<div class="min-w-0">
			<div class="flex items-center gap-2">
				<span class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-iris-500/25 to-mint-400/15 text-iris-200 ring-1 ring-inset ring-white/10">
					<Icon name="message" size={17} />
				</span>
				<div class="min-w-0">
					<h1 class="truncate text-lg font-semibold tracking-tight text-zinc-50">Ask DevFlow</h1>
					<p class="truncate text-[11px] text-zinc-500">Answers only from your Git activity.</p>
				</div>
			</div>
		</div>
		<button
			type="button"
			class="btn-secondary shrink-0 px-3 text-xs"
			onclick={newChat}
			disabled={messages.length === 0}
		>
			<Icon name="plus" size={14} /> New chat
		</button>
	</header>

	<div
		bind:this={scroller}
		class="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain rounded-2xl border border-white/6 bg-ink-900/40 p-3 sm:p-4"
		role="log"
		aria-live={sending ? 'off' : 'polite'}
		aria-label="Conversation"
	>
		{#if messages.length === 0}
			<div class="flex min-h-full flex-col items-center justify-center px-2 py-6 text-center">
				<span class="grid h-12 w-12 place-items-center rounded-2xl bg-mint-400/10 text-mint-300 ring-1 ring-inset ring-mint-400/20">
					<Icon name="sparkles" size={22} />
				</span>
				<h2 class="mt-4 text-lg font-semibold text-zinc-100">What do you want to remember?</h2>
				<p class="mt-1 max-w-sm text-sm text-zinc-500">
					Ask about projects, commits, branches or what you worked on. DevFlow reads your own
					activity — nothing else.
				</p>
				<div class="mt-6 grid w-full max-w-md gap-2 sm:grid-cols-2">
					{#each suggestions as suggestion}
						<button
							type="button"
							class="min-h-11 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-left text-[13px] text-zinc-300 transition hover:border-white/20 hover:bg-white/8 hover:text-zinc-100"
							onclick={() => submit(suggestion)}
						>
							{suggestion}
						</button>
					{/each}
				</div>
			</div>
		{:else}
			{#each messages as message (message.id)}
				<div
					class="flex gap-2.5 {message.role === 'user' ? 'justify-end' : 'justify-start'}"
				>
					{#if message.role === 'assistant'}
						<span class="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-iris-500/25 to-mint-400/15 text-mint-200 ring-1 ring-inset ring-white/10">
							<Icon name="sparkles" size={13} />
						</span>
					{/if}

					<div
						class="min-w-0 max-w-[85%] rounded-2xl px-3.5 py-2.5 sm:max-w-[78%] {message.role === 'user'
							? 'rounded-br-md bg-mint-400 text-[#06110d]'
							: 'rounded-bl-md border border-white/8 bg-ink-850 text-zinc-200'}"
					>
						{#if message.role === 'user'}
							<p class="whitespace-pre-wrap text-[14px] leading-relaxed">{message.content}</p>
						{:else if message.streaming && !message.content}
							<div class="flex items-center gap-2 text-[13px] text-zinc-400">
								<span class="flex items-center gap-1" aria-hidden="true">
									<span class="typing-dot h-1.5 w-1.5 rounded-full bg-mint-300"></span>
									<span class="typing-dot h-1.5 w-1.5 rounded-full bg-mint-300"></span>
									<span class="typing-dot h-1.5 w-1.5 rounded-full bg-mint-300"></span>
								</span>
								<span>{message.tool ? toolLabels[message.tool] ?? 'Looking that up' : 'Thinking'}…</span>
							</div>
						{:else if message.streaming}
							<p class="whitespace-pre-wrap text-[14px] leading-relaxed text-zinc-200">
								{message.content}<span class="ml-0.5 inline-block h-4 w-1 animate-pulse bg-mint-300 align-middle"></span>
							</p>
							{#if message.tool}
								<p class="mt-2 flex items-center gap-1.5 text-[11px] text-zinc-500">
									<span class="h-1.5 w-1.5 animate-pulse rounded-full bg-iris-300"></span>
									{toolLabels[message.tool] ?? 'Looking that up'}…
								</p>
							{/if}
						{:else if message.error}
							<div>
								<p class="flex items-start gap-2 text-[13px] leading-relaxed text-red-300">
									<Icon name="alert" size={15} class="mt-0.5 shrink-0" />
									<span>{message.error}</span>
								</p>
								<button
									type="button"
									class="btn-secondary mt-2.5 min-h-9 px-3 py-1.5 text-xs"
									onclick={() => retry(message)}
									disabled={sending}
								>
									<Icon name="refresh" size={13} /> Retry
								</button>
							</div>
						{:else}
							<Markdown source={message.content} />
							{#if message.tools?.length}
								<p class="mt-2 flex flex-wrap items-center gap-1 text-[10px] text-zinc-600">
									{#each message.tools as tool}
										<span class="rounded-full bg-white/5 px-2 py-0.5">{tool.replaceAll('_', ' ')}</span>
									{/each}
								</p>
							{/if}
						{/if}
					</div>
				</div>
			{/each}

			{#if sending && messages.at(-1)?.role === 'assistant' && messages.at(-1)?.streaming && messages.at(-1)?.content}
				<p class="sr-only" aria-live="polite">DevFlow is answering.</p>
			{/if}
		{/if}
	</div>

	<form
		class="flex flex-none items-end gap-2 pt-3"
		onsubmit={(event) => {
			event.preventDefault();
			submit();
		}}
	>
		<label class="sr-only" for="chat-input">Ask DevFlow a question</label>
		<textarea
			id="chat-input"
			bind:this={composer}
			bind:value={input}
			onkeydown={onKeydown}
			rows="1"
			maxlength="4000"
			placeholder="Ask about your work…"
			class="input max-h-32 min-h-11 flex-1 resize-none py-3 leading-relaxed"
		></textarea>
		<button
			type="submit"
			class="btn-primary h-11 w-11 shrink-0 p-0"
			disabled={sending || !input.trim()}
			aria-label="Send message"
		>
			<Icon name="send" size={17} />
		</button>
	</form>
	<p class="flex-none pt-1.5 text-center text-[10px] text-zinc-600">
		DevFlow reads your activity only. Press Enter to send, Shift+Enter for a new line.
	</p>
</div>
