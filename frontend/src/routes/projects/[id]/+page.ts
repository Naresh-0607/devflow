import { fetchProject } from '#lib/api';
import { swr } from '#lib/load';
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) =>
	swr(`/projects/${params.id}`, () => fetchProject(params.id));
