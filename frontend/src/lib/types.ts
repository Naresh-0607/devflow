export type ProjectStatus = 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ARCHIVED';
export type SummaryType = 'DAILY' | 'WEEKLY' | 'PROJECT';
export type EventType = 'repository_created' | 'branch_change' | 'commit' | 'push';

export interface User {
	id: string;
	email: string;
	created_at: string;
}

export interface TokenPair {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface AuthResponse {
	user: User;
	tokens: TokenPair;
}

export interface Device {
	id: string;
	name: string;
	api_key_prefix: string;
	last_seen: string | null;
	created_at: string;
}

export interface DeviceCreated extends Device {
	api_key: string;
}

export interface Project {
	id: string;
	name: string;
	description: string | null;
	status: ProjectStatus;
	started_at: string;
	completed_at: string | null;
	created_at: string;
	updated_at: string;
	last_activity_at: string | null;
	event_count: number;
	repository_count: number;
}

export interface Repository {
	id: string;
	name: string;
	remote_url: string | null;
	local_identifier: string;
	created_at: string;
}

export interface GitEvent {
	id: string;
	event_type: EventType;
	payload: Record<string, unknown>;
	created_at: string;
	repository_id: string;
	repository_name: string | null;
	project_id: string | null;
	project_name: string | null;
}

export interface Summary {
	id: string;
	project_id: string;
	summary: string;
	summary_type: SummaryType;
	created_at: string;
}

export interface ProjectDetail extends Project {
	repositories: Repository[];
	recent_events: GitEvent[];
	latest_summary: Summary | null;
}

export interface Dashboard {
	active_projects: number;
	total_projects: number;
	total_events: number;
	last_active_project: Project | null;
	recent_activity: GitEvent[];
	latest_summary: Summary | null;
}

export interface InsightFeed {
	summaries: Summary[];
	projects: Project[];
}
