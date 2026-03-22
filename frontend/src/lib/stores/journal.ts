import { writable, get } from 'svelte/store';
import { api } from '$lib/api/client';

export interface JournalEntry {
	id?: string;
	date: string;
	content: string;
	mood_score: number | null;
	energy_score: number | null;
	tags: string[];
	wins: string[];
	ai_reflection: string | null;
	word_count: number;
	created_at?: string;
	updated_at?: string;
}

function createJournalStore() {
	const entries = writable<JournalEntry[]>([]);
	const currentEntry = writable<JournalEntry | null>(null);
	const loading = writable(false);
	const saving = writable(false);

	function todayDate(): string {
		return new Date().toISOString().split('T')[0];
	}

	async function loadEntries(limit = 30) {
		loading.set(true);
		try {
			const result = await api.fetch('/journal/', { params: { limit: String(limit) } });
			entries.set(result);
		} catch {
			entries.set([]);
		}
		loading.set(false);
	}

	async function loadEntry(date: string) {
		loading.set(true);
		try {
			const result = await api.fetch(`/journal/${date}`);
			currentEntry.set(result);
		} catch {
			// No entry for this date, create blank
			currentEntry.set({
				date,
				content: '',
				mood_score: null,
				energy_score: null,
				tags: [],
				wins: [],
				ai_reflection: null,
				word_count: 0,
			});
		}
		loading.set(false);
	}

	async function saveEntry(entry: Partial<JournalEntry>) {
		saving.set(true);
		try {
			const date = entry.date || todayDate();
			const result = await api.fetch('/journal/', {
				method: 'POST',
				body: JSON.stringify({ ...entry, date }),
			});
			currentEntry.set(result);
			// Refresh entries list
			await loadEntries();
		} catch (e) {
			console.error('Failed to save journal entry:', e);
		}
		saving.set(false);
	}

	async function getReflection(date: string) {
		try {
			const result = await api.fetch(`/journal/${date}/reflect`, { method: 'POST' });
			currentEntry.update((e) => e ? { ...e, ai_reflection: result.reflection } : e);
		} catch (e) {
			console.error('Failed to get reflection:', e);
		}
	}

	return {
		entries,
		currentEntry,
		loading,
		saving,
		loadEntries,
		loadEntry,
		saveEntry,
		getReflection,
		todayDate,
	};
}

export const journal = createJournalStore();
