import type {
	AuthResponse,
	ChatHistoryMessage,
	ChatReply,
	ChatStreamHandlers,
	Dashboard,
	Device,
	DeviceCreated,
	GitEvent,
	InsightFeed,
	Project,
	ProjectDetail,
	ProjectStatus,
	Summary,
	SummaryType,
	TokenPair,
	User
} from './types';

const BASE = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const ACCESS_KEY = 'dvf_access_token';
const REFRESH_KEY = 'dvf_refresh_token';
const USER_KEY = 'dvf_user';

export class ApiError extends Error {
	status: number;

	constructor(status: number, message: string) {
		super(message);
		this.status = status;
	}
}

function isBrowser() {
	return typeof window !== 'undefined';
}

export function getAccessToken(): string | null {
	return isBrowser() ? localStorage.getItem(ACCESS_KEY) : null;
}

export function getRefreshToken(): string | null {
	return isBrowser() ? localStorage.getItem(REFRESH_KEY) : null;
}

export function getStoredUser(): User | null {
	if (!isBrowser()) return null;
	try {
		const raw = localStorage.getItem(USER_KEY);
		return raw ? (JSON.parse(raw) as User) : null;
	} catch {
		return null;
	}
}

export function saveSession(tokens: TokenPair, user?: User) {
	if (!isBrowser()) return;
	localStorage.setItem(ACCESS_KEY, tokens.access_token);
	localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
	if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

const CACHE_PREFIX = 'dvf_cache:';
const pendingPrefetches = new Map<string, { promise: Promise<unknown>; at: number }>();

function currentUserId(): string | null {
	const user = getStoredUser();
	return user?.id ?? null;
}

function cacheKey(path: string): string | null {
	const userId = currentUserId();
	return userId ? `${CACHE_PREFIX}${userId}:${path}` : null;
}

/** Read the last successful response for a path, even if it is stale. */
export function readCache<T>(path: string): T | null {
	if (!isBrowser()) return null;
	const key = cacheKey(path);
	if (!key) return null;
	try {
		const raw = localStorage.getItem(key);
		return raw ? (JSON.parse(raw) as T) : null;
	} catch {
		return null;
	}
}

export function writeCache<T>(path: string, data: T): void {
	if (!isBrowser()) return;
	const key = cacheKey(path);
	if (!key) return;
	try {
		localStorage.setItem(key, JSON.stringify(data));
	} catch {
		/* storage may be full or disabled */
	}
}

export function invalidateCache(path?: string): void {
	if (!isBrowser()) return;
	const userId = currentUserId();
	const base = userId ? `${CACHE_PREFIX}${userId}:` : CACHE_PREFIX;
	try {
		for (const key of Object.keys(localStorage)) {
			if (!key.startsWith(base)) continue;
			if (path && key !== `${base}${path}`) continue;
			localStorage.removeItem(key);
		}
	} catch {
		/* ignore */
	}
}

function clearPendingPrefetches(): void {
	pendingPrefetches.clear();
}

export function clearSession() {
	if (!isBrowser()) return;
	invalidateCache();
	clearPendingPrefetches();
	localStorage.removeItem(ACCESS_KEY);
	localStorage.removeItem(REFRESH_KEY);
	localStorage.removeItem(USER_KEY);
	try {
		// Conversation history belongs to the signed-in user.
		sessionStorage.removeItem('dvf_chat_messages');
	} catch {
		/* ignore */
	}
}

/** True when the access token exists and is not about to expire. */
export function isAccessTokenFresh(leewaySeconds = 30): boolean {
	const token = getAccessToken();
	if (!token) return false;
	try {
		const payload = JSON.parse(
			atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))
		) as { exp?: number };
		return typeof payload.exp === 'number' && payload.exp * 1000 > Date.now() + leewaySeconds * 1000;
	} catch {
		return false;
	}
}

/**
 * Start (or reuse) a request before navigation finishes. Returns cached data
 * immediately so a route can render without waiting for the network.
 */
export function prefetch<T>(path: string, loader: () => Promise<T>): T | null {
	const cached = readCache<T>(path);
	if (!isBrowser()) return cached;

	const existing = pendingPrefetches.get(path);
	if (existing && Date.now() - existing.at < 30_000) return cached;

	const promise = loader()
		.then((data) => {
			writeCache(path, data);
			return data;
		})
		.catch((error) => {
			pendingPrefetches.delete(path);
			throw error;
		});
	pendingPrefetches.set(path, { promise, at: Date.now() });
	return cached;
}

/** Consume the in-flight prefetch started by a route load function. */
export function consumePrefetch<T>(path: string): Promise<T> | null {
	const item = pendingPrefetches.get(path);
	if (!item) return null;
	pendingPrefetches.delete(path);
	return item.promise as Promise<T>;
}

/** Wake a sleeping Render instance without blocking the UI. */
export function wakeBackend(): void {
	if (!isBrowser()) return;
	try {
		if (sessionStorage.getItem('dvf_health_ping') === '1') return;
		sessionStorage.setItem('dvf_health_ping', '1');
	} catch {
		/* ignore */
	}
	fetch(`${BASE}/health`, { cache: 'no-store' }).catch(() => {
		/* a cold backend will retry on the first real request */
	});
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
	const refresh_token = getRefreshToken();
	if (!refresh_token) return false;
	if (refreshInFlight) return refreshInFlight;

	refreshInFlight = (async () => {
		try {
			const response = await fetch(`${BASE}/api/v1/auth/refresh`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ refresh_token })
			});
			if (!response.ok) {
				clearSession();
				return false;
			}
			const tokens = (await response.json()) as TokenPair;
			saveSession(tokens);
			return true;
		} catch {
			return false;
		} finally {
			refreshInFlight = null;
		}
	})();

	return refreshInFlight;
}

async function parseError(response: Response): Promise<string> {
	try {
		const body = await response.json();
		if (typeof body?.detail === 'string') return body.detail;
		if (Array.isArray(body?.detail)) {
			return body.detail.map((item: { msg?: string }) => item.msg ?? 'Invalid input').join(', ');
		}
	} catch {
		/* ignore non-JSON errors */
	}
	return `Request failed (${response.status})`;
}

export async function api<T>(
	path: string,
	options: RequestInit = {},
	retry = true
): Promise<T> {
	const headers = new Headers(options.headers);
	if (options.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	const token = getAccessToken();
	if (token) headers.set('Authorization', `Bearer ${token}`);

	const response = await fetch(`${BASE}/api/v1${path}`, { ...options, headers });

	if (response.status === 401 && retry && getRefreshToken()) {
		const refreshed = await refreshSession();
		if (refreshed) return api<T>(path, options, false);
		clearSession();
		window.dispatchEvent(new CustomEvent('devflow:unauthorized'));
	}

	if (!response.ok) {
		throw new ApiError(response.status, await parseError(response));
	}
	if (response.status === 204) return undefined as T;
	return (await response.json()) as T;
}

// ---------- Auth ----------
export async function register(email: string, password: string): Promise<AuthResponse> {
	const data = await api<AuthResponse>(
		'/auth/register',
		{ method: 'POST', body: JSON.stringify({ email, password }) },
		false
	);
	saveSession(data.tokens, data.user);
	return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
	const data = await api<AuthResponse>(
		'/auth/login',
		{ method: 'POST', body: JSON.stringify({ email, password }) },
		false
	);
	saveSession(data.tokens, data.user);
	return data;
}

export async function logoutRequest(): Promise<void> {
	const refresh_token = getRefreshToken();
	if (refresh_token) {
		try {
			await api<void>(
				'/auth/logout',
				{ method: 'POST', body: JSON.stringify({ refresh_token }) },
				false
			);
		} catch {
			/* logging out locally is enough */
		}
	}
	clearSession();
}

export async function fetchMe(): Promise<User> {
	return api<User>('/auth/me');
}

// ---------- Dashboard / projects ----------
export async function fetchDashboard(): Promise<Dashboard> {
	return api<Dashboard>('/dashboard');
}

export async function fetchProjects(): Promise<Project[]> {
	return api<Project[]>('/projects');
}

export async function createProject(payload: {
	name: string;
	description?: string;
}): Promise<Project> {
	const project = await api<Project>('/projects', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
	invalidateCache();
	return project;
}

export async function fetchProject(id: string): Promise<ProjectDetail> {
	return api<ProjectDetail>(`/projects/${id}`);
}

export async function updateProject(
	id: string,
	payload: { name?: string; description?: string; status?: ProjectStatus }
): Promise<Project> {
	const project = await api<Project>(`/projects/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
	invalidateCache();
	return project;
}

export async function deleteProject(id: string): Promise<void> {
	await api<void>(`/projects/${id}`, { method: 'DELETE' });
	invalidateCache();
}

export async function fetchEvents(projectId?: string): Promise<GitEvent[]> {
	const query = projectId ? `?project_id=${projectId}` : '';
	return api<GitEvent[]>(`/events${query}`);
}

// ---------- AI insights ----------
export async function fetchInsights(): Promise<InsightFeed> {
	return api<InsightFeed>('/insights');
}

// ---------- Chat ----------
export function getUserTimezone(): string {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
	} catch {
		return 'UTC';
	}
}

type ChatStreamPayload = {
	message: string;
	history: ChatHistoryMessage[];
	timezone?: string;
};

/**
 * Stream a chat answer over SSE. Falls back to a plain JSON response if the
 * backend does not negotiate an event stream.
 */
export async function streamChat(
	payload: ChatStreamPayload,
	handlers: ChatStreamHandlers,
	retry = true
): Promise<void> {
	const headers = new Headers({
		'Content-Type': 'application/json',
		Accept: 'text/event-stream'
	});
	const token = getAccessToken();
	if (token) headers.set('Authorization', `Bearer ${token}`);

	const response = await fetch(`${BASE}/api/v1/chat`, {
		method: 'POST',
		headers,
		body: JSON.stringify({
			message: payload.message,
			history: payload.history,
			timezone: payload.timezone ?? getUserTimezone(),
			stream: true
		})
	});

	if (response.status === 401 && retry && getRefreshToken()) {
		const refreshed = await refreshSession();
		if (refreshed) return streamChat(payload, handlers, false);
		clearSession();
		window.dispatchEvent(new CustomEvent('devflow:unauthorized'));
	}

	if (!response.ok) {
		throw new ApiError(response.status, await parseError(response));
	}

	if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) {
		const body = (await response.json()) as ChatReply;
		handlers.onToken(body.answer);
		handlers.onDone(body.answer, body.tools_used ?? []);
		return;
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	let answer = '';
	let tools: string[] = [];
	let finished = false;

	const dispatch = (frame: string) => {
		const lines = frame.split(/\r?\n/);
		const eventLine = lines.find((line) => line.startsWith('event:'));
		const data = lines
			.filter((line) => line.startsWith('data:'))
			.map((line) => line.slice(5).trimStart())
			.join('\n');
		if (!data) return;

		let parsed: {
			type?: string;
			content?: string;
			name?: string;
			answer?: string;
			tools_used?: string[];
			message?: string;
		};
		try {
			parsed = JSON.parse(data);
		} catch {
			return;
		}
		const event = eventLine?.slice(6).trim() || parsed.type;

		if (event === 'token' && parsed.content) {
			answer += parsed.content;
			handlers.onToken(parsed.content);
		} else if (event === 'tool' && parsed.name) {
			handlers.onTool?.(parsed.name);
		} else if (event === 'done') {
			answer = parsed.answer ?? answer;
			tools = parsed.tools_used ?? tools;
			finished = true;
			handlers.onDone(answer, tools);
		} else if (event === 'error') {
			throw new Error(parsed.message ?? 'The chat stream failed.');
		}
	};

	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const frames = buffer.split(/\r?\n\r?\n/);
			buffer = frames.pop() ?? '';
			for (const frame of frames) dispatch(frame);
		}
		buffer += decoder.decode();
		if (buffer.trim()) dispatch(buffer);
		if (!finished && answer) handlers.onDone(answer, tools);
	} finally {
		reader.releaseLock();
	}
}

export async function generateSummary(
	projectId: string,
	summaryType: SummaryType
): Promise<Summary> {
	const summary = await api<Summary>(`/projects/${projectId}/summaries`, {
		method: 'POST',
		body: JSON.stringify({ summary_type: summaryType })
	});
	invalidateCache();
	return summary;
}

// ---------- Devices ----------
export async function fetchDevices(): Promise<Device[]> {
	return api<Device[]>('/devices');
}

export async function createDevice(name: string): Promise<DeviceCreated> {
	return api<DeviceCreated>('/devices', { method: 'POST', body: JSON.stringify({ name }) });
}

export async function revokeDevice(id: string): Promise<void> {
	return api<void>(`/devices/${id}`, { method: 'DELETE' });
}
