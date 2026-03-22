import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';
import { api } from '$lib/api/client';

export interface ChatMessage {
	id?: string;
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	flowPrompt?: FlowPrompt;
}

export interface FlowPrompt {
	flow_id: string;
	step: string;
	prompt: string;
	input_type: 'text' | 'slider' | 'choice' | 'mood_picker';
	options?: string[];
	min_val?: number;
	max_val?: number;
}

const CONVO_KEY = 'mirror_conversation_id';

function createChatStore() {
	const messages = writable<ChatMessage[]>([]);
	const connected = writable(false);
	const conversationId = writable<string | null>(
		browser ? localStorage.getItem(CONVO_KEY) : null
	);
	const activeFlow = writable<{ flowId: string; step: string } | null>(null);
	const isTyping = writable(false);
	const historyLoaded = writable(false);

	let ws: WebSocket | null = null;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	let typingTimer: ReturnType<typeof setTimeout> | null = null;

	async function loadHistory() {
		const convoId = get(conversationId);
		if (!convoId) {
			historyLoaded.set(true);
			return;
		}

		try {
			const msgs = await api.getMessages(convoId, 50);
			const chatMsgs: ChatMessage[] = msgs.map((m: any) => ({
				id: m.id,
				role: m.role as 'user' | 'assistant',
				content: m.content,
				timestamp: m.created_at,
			}));
			messages.set(chatMsgs);
		} catch {
			// Conversation might not exist anymore, start fresh
			localStorage.removeItem(CONVO_KEY);
			conversationId.set(null);
			messages.set([]);
		}
		historyLoaded.set(true);
	}

	function connect() {
		if (ws?.readyState === WebSocket.OPEN) return;

		const url = api.getWsUrl();
		ws = new WebSocket(url);

		ws.onopen = () => {
			connected.set(true);
		};

		ws.onmessage = (event) => {
			const data = JSON.parse(event.data);
			handleServerMessage(data);
		};

		ws.onclose = () => {
			connected.set(false);
			// Reconnect if user is still authenticated
			if (reconnectTimer) clearTimeout(reconnectTimer);
			reconnectTimer = setTimeout(() => {
				if (browser && localStorage.getItem('access_token')) {
					connect();
				}
			}, 3000);
		};

		ws.onerror = () => {
			connected.set(false);
		};
	}

	function handleServerMessage(data: any) {
		if (typingTimer) clearTimeout(typingTimer);
		isTyping.set(false);

		if (data.type === 'pong') return;

		if (data.type === 'message') {
			const msg: ChatMessage = {
				role: 'assistant',
				content: data.content,
				timestamp: data.timestamp || new Date().toISOString(),
			};

			if (data.flow_prompt) {
				msg.flowPrompt = data.flow_prompt;
			}

			messages.update((msgs) => [...msgs, msg]);

			// Persist conversation ID
			if (data.metadata?.conversation_id) {
				const convoId = data.metadata.conversation_id;
				conversationId.set(convoId);
				if (browser) {
					localStorage.setItem(CONVO_KEY, convoId);
				}
			}

			if (data.metadata?.flow_active !== undefined) {
				if (data.metadata.flow_active && data.flow_prompt) {
					activeFlow.set({
						flowId: data.metadata.flow_id,
						step: data.flow_prompt.step,
					});
				} else if (!data.metadata.flow_active) {
					activeFlow.set(null);
				}
			}
		}
	}

	function sendMessage(content: string) {
		if (!ws || ws.readyState !== WebSocket.OPEN) return;

		const msg: ChatMessage = {
			role: 'user',
			content,
			timestamp: new Date().toISOString(),
		};
		messages.update((msgs) => [...msgs, msg]);
		isTyping.set(true);

		// Typing timeout — clear after 30s if no response
		if (typingTimer) clearTimeout(typingTimer);
		typingTimer = setTimeout(() => {
			isTyping.set(false);
			messages.update((msgs) => [
				...msgs,
				{
					role: 'assistant' as const,
					content: 'Mirror is taking longer than usual. Try sending your message again.',
					timestamp: new Date().toISOString(),
				},
			]);
		}, 30000);

		ws.send(
			JSON.stringify({
				type: 'message',
				content,
				conversation_id: get(conversationId),
			})
		);
	}

	function sendFlowResponse(flowId: string, step: string, value: any) {
		if (!ws || ws.readyState !== WebSocket.OPEN) return;

		const displayValue = Array.isArray(value) ? value.join(', ') : String(value);
		const msg: ChatMessage = {
			role: 'user',
			content: displayValue,
			timestamp: new Date().toISOString(),
		};
		messages.update((msgs) => [...msgs, msg]);
		isTyping.set(true);

		ws.send(
			JSON.stringify({
				type: 'message',
				content: String(value),
				conversation_id: get(conversationId),
			})
		);
	}

	function pause() {
		// Called when navigating away - close WS but KEEP messages and conversationId
		if (reconnectTimer) clearTimeout(reconnectTimer);
		reconnectTimer = null;
		ws?.close();
		ws = null;
		connected.set(false);
	}

	function logout() {
		// Full reset - only on logout
		pause();
		messages.set([]);
		conversationId.set(null);
		activeFlow.set(null);
		historyLoaded.set(false);
		if (browser) localStorage.removeItem(CONVO_KEY);
	}

	function startNewConversation() {
		messages.set([]);
		conversationId.set(null);
		activeFlow.set(null);
		historyLoaded.set(true);
		if (browser) localStorage.removeItem(CONVO_KEY);
	}

	return {
		messages,
		connected,
		conversationId,
		activeFlow,
		isTyping,
		historyLoaded,
		connect,
		loadHistory,
		sendMessage,
		sendFlowResponse,
		pause,
		logout,
		startNewConversation,
	};
}

export const chat = createChatStore();
