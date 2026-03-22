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

	function hydrateFromToken(token: string): boolean {
		const payload = decodeJwt(token);
		if (!payload) return false;
		set({
			email: payload.email || payload.sub || '',
			name: payload.name || '',
		});
		return true;
	}

	async function tryRefresh(): Promise<boolean> {
		const refreshToken = localStorage.getItem('refresh_token');
		if (!refreshToken) return false;

		try {
			const apiBase = import.meta.env.VITE_API_URL || '/api';
			const res = await fetch(`${apiBase}/auth/refresh`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ refresh_token: refreshToken }),
			});

			if (!res.ok) return false;

			const data = await res.json();
			localStorage.setItem('access_token', data.access_token);
			localStorage.setItem('refresh_token', data.refresh_token);
			return hydrateFromToken(data.access_token);
		} catch {
			return false;
		}
	}

	function clearAll() {
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
		set(null);
	}

	return {
		subscribe,
		set,
		login(user: User) {
			set(user);
		},
		logout() {
			if (browser) {
				import('$lib/stores/chat').then(({ chat }) => chat.logout());
				clearAll();
			} else {
				set(null);
			}
		},
		async init() {
			if (!browser) return;

			const token = localStorage.getItem('access_token');
			if (!token) {
				// No access token — try refresh
				const refreshed = await tryRefresh();
				if (!refreshed) {
					set(null);
				}
				return;
			}

			const payload = decodeJwt(token);
			if (!payload) {
				clearAll();
				return;
			}

			// Check if expired
			if (payload.exp && payload.exp * 1000 < Date.now()) {
				// Access token expired — try refresh instead of clearing everything
				const refreshed = await tryRefresh();
				if (!refreshed) {
					clearAll();
				}
				return;
			}

			// Token is valid — hydrate user from payload
			hydrateFromToken(token);
		},
	};
}

export const user = createAuthStore();
export const isAuthenticated = derived(user, ($user) => $user !== null);
