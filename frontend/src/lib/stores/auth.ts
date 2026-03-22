import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

interface User {
	email: string;
	name: string;
}

function decodeJwt(token: string): { exp?: number; sub?: string; name?: string; email?: string } | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;
		const payload = JSON.parse(atob(parts[1]));
		return payload;
	} catch {
		return null;
	}
}

function createAuthStore() {
	const { subscribe, set } = writable<User | null>(null);

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
					return;
				}

				const payload = decodeJwt(token);
				if (!payload) {
					// Token is corrupted — clear and force re-login
					localStorage.removeItem('access_token');
					localStorage.removeItem('refresh_token');
					set(null);
					return;
				}

				// Check if expired
				if (payload.exp && payload.exp * 1000 < Date.now()) {
					// Token expired — clear and force re-login
					localStorage.removeItem('access_token');
					localStorage.removeItem('refresh_token');
					set(null);
					return;
				}

				// Token is valid — hydrate user from payload
				set({
					email: payload.email || payload.sub || '',
					name: payload.name || '',
				});
			}
		},
	};
}

export const user = createAuthStore();
export const isAuthenticated = derived(user, ($user) => $user !== null);
