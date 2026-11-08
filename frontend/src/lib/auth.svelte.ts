import { goto } from '$app/navigation';
import {
	clearSession,
	fetchMe,
	getAccessToken,
	getStoredUser,
	logoutRequest,
	register as apiRegister,
	login as apiLogin,
	saveSession
} from './api';
import type { AuthResponse, User } from './types';

class AuthStore {
	user = $state<User | null>(null);
	ready = $state(false);

	get isAuthenticated() {
		return this.user !== null;
	}

	async init() {
		if (this.ready) return;
		if (typeof window === 'undefined') return;
		if (!getAccessToken()) {
			this.ready = true;
			return;
		}

		this.user = getStoredUser();
		try {
			this.user = await fetchMe();
		} catch {
			this.user = null;
			clearSession();
		} finally {
			this.ready = true;
		}
	}

	async login(email: string, password: string) {
		const data = await apiLogin(email, password);
		this.apply(data);
	}

	async register(email: string, password: string) {
		const data = await apiRegister(email, password);
		this.apply(data);
	}

	apply(data: AuthResponse) {
		saveSession(data.tokens, data.user);
		this.user = data.user;
		this.ready = true;
	}

	async logout() {
		await logoutRequest();
		this.user = null;
		await goto('/login');
	}
}

export const auth = new AuthStore();
