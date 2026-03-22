import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

interface User {
	email: string;
	name: string;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<User | null>(null);

	return {
		subscribe,
		set,
		login(user: User) {
			set(user);
		},
		logout() {
			if (browser) {
				// Clear chat state
				import('$lib/stores/chat').then(({ chat }) => chat.logout());
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
			}
			set(null);
		},
		init() {
			if (browser) {
				const token = localStorage.getItem('access_token');
				if (!token) {
					set(null);
				}
			}
		},
	};
}

export const user = createAuthStore();
export const isAuthenticated = derived(user, ($user) => $user !== null);
