import { writable, get } from 'svelte/store';
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

function createChatStore() {
	const messages = writable<ChatMessage[]>([]);
	const connected = writable(false);
	const conversationId = writable<string | null>(null);
	const activeFlow = writable<{ flowId: string; step: string } | null>(null);
	const isTyping = writable(false);

	let ws: WebSocket | null = null;

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
			// Reconnect after 3 seconds
			setTimeout(() => {
				const token = localStorage.getItem('access_token');
				if (token) connect();
			}, 3000);
		};

		ws.onerror = () => {
			connected.set(false);
		};
	}

	function handleServerMessage(data: any) {
		isTyping.set(false);

		if (data.type === 'pong') return;

		if (data.type === 'message') {
			const msg: ChatMessage = {
				role: 'assistant',
				content: data.content,
				timestamp: data.timestamp || new Date().toISOString(),
			};

			// Check for flow prompt
			if (data.flow_prompt) {
				msg.flowPrompt = data.flow_prompt;
			}

			messages.update((msgs) => [...msgs, msg]);

			// Update conversation state
			if (data.metadata?.conversation_id) {
				conversationId.set(data.metadata.conversation_id);
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

		// Show user's response as a message
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

	function disconnect() {
		ws?.close();
		ws = null;
		connected.set(false);
		messages.set([]);
		conversationId.set(null);
		activeFlow.set(null);
	}

	return {
		messages,
		connected,
		conversationId,
		activeFlow,
		isTyping,
		connect,
		sendMessage,
		sendFlowResponse,
		disconnect,
	};
}

export const chat = createChatStore();
