export type EventMeta = {
	icon: string;
	/** Tinted icon square: border + background + text. */
	tone: string;
	/** Solid dot used on the timeline. */
	dot: string;
	label: string;
};

const EVENT_META: Record<string, EventMeta> = {
	commit: {
		icon: 'commit',
		tone: 'border-info/30 bg-info/10 text-info',
		dot: 'bg-info',
		label: 'Commit'
	},
	branch_change: {
		icon: 'branch',
		tone: 'border-warning/30 bg-warning/10 text-warning',
		dot: 'bg-warning',
		label: 'Branch'
	},
	push: {
		icon: 'push',
		tone: 'border-success/30 bg-success/10 text-success',
		dot: 'bg-success',
		label: 'Push'
	},
	repository_created: {
		icon: 'folder-plus',
		tone: 'border-violet/30 bg-violet/10 text-violet',
		dot: 'bg-violet',
		label: 'Repository'
	}
};

export function eventMeta(type: string): EventMeta {
	return (
		EVENT_META[type] ?? {
			icon: 'code',
			tone: 'border-border bg-raised text-muted',
			dot: 'bg-muted',
			label: 'Event'
		}
	);
}

/** Short commit hash from an event payload, when the agent recorded one. */
export function shortHash(payload: Record<string, unknown>): string | null {
	const sha = payload.sha ?? payload.hash;
	return typeof sha === 'string' && sha.length >= 7 ? sha.slice(0, 7) : null;
}

/** Distinct branches present in a list of events. */
export function eventBranches(events: Array<{ payload: Record<string, unknown> }>): string[] {
	const branches = new Set<string>();
	for (const event of events) {
		const value = event.payload.branch ?? event.payload.to_branch;
		if (typeof value === 'string' && value.trim()) branches.add(value);
	}
	return [...branches];
}
