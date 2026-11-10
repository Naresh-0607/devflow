export type ThemeMode = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'dvf_theme';
const MODES: ThemeMode[] = ['system', 'light', 'dark'];

function prefersDark(): boolean {
	return typeof window !== 'undefined'
		? window.matchMedia('(prefers-color-scheme: dark)').matches
		: true;
}

function resolve(mode: ThemeMode): 'light' | 'dark' {
	if (mode === 'light') return 'light';
	if (mode === 'dark') return 'dark';
	return prefersDark() ? 'dark' : 'light';
}

class ThemeStore {
	mode = $state<ThemeMode>('system');
	resolved = $state<'light' | 'dark'>('dark');
	private started = false;

	init() {
		if (this.started || typeof window === 'undefined') return;
		this.started = true;

		const stored = localStorage.getItem(STORAGE_KEY);
		this.mode = MODES.includes(stored as ThemeMode) ? (stored as ThemeMode) : 'system';
		this.apply();

		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
			if (this.mode === 'system') this.apply();
		});
	}

	set(mode: ThemeMode) {
		this.mode = mode;
		if (typeof window !== 'undefined') {
			try {
				localStorage.setItem(STORAGE_KEY, mode);
			} catch {
				/* storage may be unavailable */
			}
		}
		this.apply();
	}

	cycle() {
		const index = MODES.indexOf(this.mode);
		this.set(MODES[(index + 1) % MODES.length]);
	}

	private apply() {
		if (typeof window === 'undefined') return;
		this.resolved = resolve(this.mode);
		const light = this.resolved === 'light';
		document.documentElement.classList.toggle('light', light);
		document.documentElement.style.colorScheme = this.resolved;
		document.documentElement.dataset.theme = this.mode;
		const meta = document.querySelector('meta[name="theme-color"]');
		if (meta) meta.setAttribute('content', light ? '#FAFAF9' : '#0B0D10');
	}
}

export const theme = new ThemeStore();
