import { fetchDashboard } from '#lib/api';
import { swr } from '#lib/load';
import type { PageLoad } from './$types';

export const load: PageLoad = () => swr('/dashboard', fetchDashboard);
