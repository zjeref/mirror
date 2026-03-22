const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface FetchOptions extends RequestInit {
	params?: Record<string, string>;
}

class ApiClient {
	private getToken(): string | null {
		if (typeof window === 'undefined') return null;
		return localStorage.getItem('access_token');
	}

	private getRefreshToken(): string | null {
		if (typeof window === 'undefined') return null;
		return localStorage.getItem('refresh_token');
	}

	private setTokens(access: string, refresh: string) {
		localStorage.setItem('access_token', access);
		localStorage.setItem('refresh_token', refresh);
	}

	clearTokens() {
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
	}

	private async refreshAccessToken(): Promise<boolean> {
		const refreshToken = this.getRefreshToken();
		if (!refreshToken) return false;

		try {
			const res = await fetch(`${API_BASE}/auth/refresh`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ refresh_token: refreshToken }),
			});

			if (!res.ok) return false;

			const data = await res.json();
			this.setTokens(data.access_token, data.refresh_token);
			return true;
		} catch {
			return false;
		}
	}

	async fetch<T = any>(path: string, options: FetchOptions = {}): Promise<T> {
		const { params, ...fetchOptions } = options;

		let url = `${API_BASE}${path}`;
		if (params) {
			const searchParams = new URLSearchParams(params);
			url += `?${searchParams}`;
		}

		const token = this.getToken();
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(options.headers as Record<string, string>),
		};
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		let res = await fetch(url, { ...fetchOptions, headers });

		// Auto-refresh on 401
		if (res.status === 401) {
			const refreshed = await this.refreshAccessToken();
			if (refreshed) {
				headers['Authorization'] = `Bearer ${this.getToken()}`;
				res = await fetch(url, { ...fetchOptions, headers });
			} else {
				this.clearTokens();
				// Sync auth store so UI updates immediately
				const { user } = await import('$lib/stores/auth');
				user.set(null);
				if (typeof window !== 'undefined') {
					window.location.href = '/login';
				}
				throw new Error('Session expired');
			}
		}

		if (!res.ok) {
			const error = await res.json().catch(() => ({ detail: 'Request failed' }));
			throw new Error(error.detail || `HTTP ${res.status}`);
		}

		return res.json();
	}

	// Auth
	async register(email: string, name: string, password: string) {
		const data = await this.fetch<{ access_token: string; refresh_token: string }>(
			'/auth/register',
			{
				method: 'POST',
				body: JSON.stringify({ email, name, password }),
			}
		);
		this.setTokens(data.access_token, data.refresh_token);
		return data;
	}

	async login(email: string, password: string) {
		const data = await this.fetch<{ access_token: string; refresh_token: string }>(
			'/auth/login',
			{
				method: 'POST',
				body: JSON.stringify({ email, password }),
			}
		);
		this.setTokens(data.access_token, data.refresh_token);
		return data;
	}

	// Dashboard
	async getDashboard() {
		return this.fetch('/dashboard/summary');
	}

	async getMoodTrends(days = 30) {
		return this.fetch('/dashboard/mood-trends', { params: { days: String(days) } });
	}

	async getLifeAreas() {
		return this.fetch('/dashboard/life-areas');
	}

	async getPatterns() {
		return this.fetch('/dashboard/patterns');
	}

	async getHabits() {
		return this.fetch('/dashboard/habits');
	}

	// Habits
	async createHabit(data: {
		name: string;
		anchor: string;
		tiny_behavior: string;
		life_area: string;
	}) {
		return this.fetch('/habits', { method: 'POST', body: JSON.stringify(data) });
	}

	async logHabit(habitId: string, completed: boolean, versionDone?: string) {
		return this.fetch(`/habits/${habitId}/log`, {
			method: 'POST',
			body: JSON.stringify({ completed, version_done: versionDone }),
		});
	}

	// Suggestions
	async feedbackSuggestion(
		suggestionId: string,
		status: string,
		rating?: number
	) {
		return this.fetch(`/suggestions/${suggestionId}/feedback`, {
			method: 'POST',
			body: JSON.stringify({ status, effectiveness_rating: rating }),
		});
	}

	// Conversations
	async getConversations(limit = 20) {
		return this.fetch('/chat/conversations', { params: { limit: String(limit) } });
	}

	async getMessages(conversationId: string, limit = 50) {
		return this.fetch(`/chat/conversations/${conversationId}/messages`, {
			params: { limit: String(limit) },
		});
	}

	// Notifications
	async getNotificationPreferences() {
		return this.fetch('/notifications/preferences');
	}

	async updateNotificationPreferences(prefs: Record<string, any>) {
		return this.fetch('/notifications/preferences', {
			method: 'PUT',
			body: JSON.stringify(prefs),
		});
	}

	async subscribePush(subscription: PushSubscriptionJSON) {
		return this.fetch('/notifications/subscribe', {
			method: 'POST',
			body: JSON.stringify({ subscription }),
		});
	}

	// Screening
	async getScreeningHistory() {
		return this.fetch('/screening/history');
	}

	// Protocol
	async getCurrentProtocol() {
		return this.fetch('/protocols/current');
	}

	async getPendingHomework() {
		return this.fetch('/homework/pending');
	}

	async completeHomework(homeworkId: string, response: string) {
		return this.fetch(`/homework/${homeworkId}/complete`, {
			method: 'POST',
			body: JSON.stringify({ response }),
		});
	}

	// WebSocket
	getWsUrl(): string {
		const token = this.getToken();
		if (API_BASE.startsWith('http')) {
			// Production: convert http(s) URL to ws(s)
			const wsBase = API_BASE.replace(/^http/, 'ws');
			return `${wsBase}/chat/ws?token=${token}`;
		}
		// Dev: use current host with proxy
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		return `${protocol}//${window.location.host}/api/chat/ws?token=${token}`;
	}
}

export const api = new ApiClient();
