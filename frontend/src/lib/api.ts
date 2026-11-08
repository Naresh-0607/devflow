import type {
	AuthResponse,
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

export function clearSession() {
	if (!isBrowser()) return;
	localStorage.removeItem(ACCESS_KEY);
	localStorage.removeItem(REFRESH_KEY);
	localStorage.removeItem(USER_KEY);
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
	return api<Project>('/projects', { method: 'POST', body: JSON.stringify(payload) });
}

export async function fetchProject(id: string): Promise<ProjectDetail> {
	return api<ProjectDetail>(`/projects/${id}`);
}

export async function updateProject(
	id: string,
	payload: { name?: string; description?: string; status?: ProjectStatus }
): Promise<Project> {
	return api<Project>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export async function deleteProject(id: string): Promise<void> {
	return api<void>(`/projects/${id}`, { method: 'DELETE' });
}

export async function fetchEvents(projectId?: string): Promise<GitEvent[]> {
	const query = projectId ? `?project_id=${projectId}` : '';
	return api<GitEvent[]>(`/events${query}`);
}

// ---------- AI insights ----------
export async function fetchInsights(): Promise<InsightFeed> {
	return api<InsightFeed>('/insights');
}

export async function generateSummary(
	projectId: string,
	summaryType: SummaryType
): Promise<Summary> {
	return api<Summary>(`/projects/${projectId}/summaries`, {
		method: 'POST',
		body: JSON.stringify({ summary_type: summaryType })
	});
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
