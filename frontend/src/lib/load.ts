import { readCache, writeCache } from './api';

export type SwrResult<T> = {
	/** Last successful response, shown immediately if present. */
	cached: T | null;
	/** Refreshed data; route loads return before the network settles. */
	fresh: Promise<{ data?: T; error?: string }>;
};

/**
 * Stale-while-revalidate loading for SvelteKit route loads.
 *
 * The load function resolves immediately with cached data (or `null`) so
 * navigation is never blocked on the network. The page awaits `fresh` and
 * swaps in new data when it arrives.
 */
export function swr<T>(path: string, loader: () => Promise<T>): SwrResult<T> {
	const cached = readCache<T>(path);
	const fresh = loader()
		.then((data) => {
			writeCache(path, data);
			return { data };
		})
		.catch((error: unknown) => ({
			error: error instanceof Error ? error.message : 'Could not load this page.'
		}));
	return { cached, fresh };
}
