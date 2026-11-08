export function relativeTime(value: string | null | undefined): string {
	if (!value) return 'no activity yet';
	const then = new Date(value).getTime();
	if (Number.isNaN(then)) return 'unknown';
	const diff = Math.max(0, Date.now() - then);
	const minutes = Math.floor(diff / 60000);
	if (minutes < 1) return 'just now';
	if (minutes < 60) return `${minutes}m ago`;
	const hours = Math.floor(minutes / 60);
	if (hours < 24) return `${hours}h ago`;
	const days = Math.floor(hours / 24);
	if (days === 1) return 'yesterday';
	if (days < 30) return `${days}d ago`;
	const months = Math.floor(days / 30);
	if (months < 12) return `${months}mo ago`;
	return `${Math.floor(months / 12)}y ago`;
}

export function daysSince(value: string | null | undefined): number {
	if (!value) return 0;
	const then = new Date(value).getTime();
	if (Number.isNaN(then)) return 0;
	return Math.max(0, Math.floor((Date.now() - then) / 86400000));
}

export function formatDate(value: string | null | undefined): string {
	if (!value) return '—';
	return new Date(value).toLocaleDateString(undefined, {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});
}

export function formatDateTime(value: string | null | undefined): string {
	if (!value) return '—';
	return new Date(value).toLocaleString(undefined, {
		day: 'numeric',
		month: 'short',
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function eventTitle(type: string, payload: Record<string, unknown>): string {
	const message = typeof payload.message === 'string' ? payload.message : null;
	const branch = typeof payload.branch === 'string' ? payload.branch : null;
	const toBranch = typeof payload.to_branch === 'string' ? payload.to_branch : branch;
	const fromBranch = typeof payload.from_branch === 'string' ? payload.from_branch : null;

	switch (type) {
		case 'commit':
			return message ?? 'Committed changes';
		case 'branch_change':
			if (fromBranch && toBranch) return `Switched ${fromBranch} → ${toBranch}`;
			return `Checked out ${toBranch ?? 'a branch'}`;
		case 'push':
			return `Pushed ${branch ?? 'branch'} to remote`;
		case 'repository_created':
			return 'Repository created';
		default:
			return type;
	}
}

export function eventBranch(payload: Record<string, unknown>): string | null {
	const value = payload.branch ?? payload.to_branch;
	return typeof value === 'string' ? value : null;
}

const STATUS_STYLES: Record<string, string> = {
	ACTIVE: 'bg-mint-400/10 text-mint-300 ring-mint-400/30',
	PAUSED: 'bg-amber-400/10 text-amber-300 ring-amber-400/30',
	COMPLETED: 'bg-sky-400/10 text-sky-300 ring-sky-400/30',
	ARCHIVED: 'bg-white/5 text-zinc-400 ring-white/10'
};

export function statusStyle(status: string): string {
	return STATUS_STYLES[status] ?? STATUS_STYLES.ARCHIVED;
}
