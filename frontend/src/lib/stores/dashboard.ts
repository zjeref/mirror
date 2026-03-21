import { writable } from 'svelte/store';
import { api } from '$lib/api/client';

export interface DashboardData {
	current_mood: number | null;
	mood_trend: string | null;
	mood_data_points: { date: string; score: number }[];
	current_energy: number | null;
	avg_energy_7d: number | null;
	life_area_scores: { area: string; score: number; trend: string; data_points: number }[];
	active_habits: { id: string; name: string; streak: number; total_completions: number }[];
	recent_patterns: {
		id: string;
		pattern_type: string;
		description: string;
		confidence: number;
		actionable_insight: string | null;
	}[];
	pending_suggestions: any[];
	suggestion_effectiveness: number | null;
	days_active: number;
	total_check_ins: number;
	last_check_in: string | null;
}

function createDashboardStore() {
	const data = writable<DashboardData | null>(null);
	const loading = writable(false);
	const error = writable<string | null>(null);

	async function load() {
		loading.set(true);
		error.set(null);
		try {
			const result = await api.getDashboard();
			data.set(result);
		} catch (e: any) {
			error.set(e.message);
		} finally {
			loading.set(false);
		}
	}

	return { data, loading, error, load };
}

export const dashboard = createDashboardStore();
