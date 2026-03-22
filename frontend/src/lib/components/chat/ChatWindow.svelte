<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { chat } from '$lib/stores/chat';
	import MessageBubble from './MessageBubble.svelte';
	import TypingIndicator from './TypingIndicator.svelte';
	import QuickReply from './QuickReply.svelte';
	import EnergySlider from './EnergySlider.svelte';

	let messagesContainer: HTMLDivElement;
	let inputText = $state('');

	const messages = chat.messages;
	const isTyping = chat.isTyping;
	const connected = chat.connected;
	const activeFlow = chat.activeFlow;
	const historyLoaded = chat.historyLoaded;

	onMount(async () => {
		// Load conversation history from DB first
		if (!$historyLoaded) {
			await chat.loadHistory();
		}
		// Then connect WebSocket
		chat.connect();

		return () => chat.pause(); // Pause, don't destroy
	});

	// Auto-scroll to bottom
	$effect(() => {
		if ($messages.length || $isTyping) {
			tick().then(() => {
				if (messagesContainer) {
					messagesContainer.scrollTop = messagesContainer.scrollHeight;
				}
			});
		}
	});

	function handleSend() {
		const text = inputText.trim();
		if (!text) return;
		chat.sendMessage(text);
		inputText = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleQuickReply(value: string) {
		chat.sendMessage(value);
	}

	function handleSlider(value: number) {
		chat.sendMessage(String(value));
	}

	function handleNewChat() {
		chat.startNewConversation();
	}

	// Get the last flow prompt from messages
	const lastFlowPrompt = $derived(
		(() => {
			for (let i = $messages.length - 1; i >= 0; i--) {
				if ($messages[i].flowPrompt) return $messages[i].flowPrompt;
			}
			return null;
		})()
	);

	const showFlowWidget = $derived($activeFlow && lastFlowPrompt);
</script>

<div class="flex flex-col h-full">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-2 border-b border-[var(--color-border)]">
		<span class="text-sm text-slate-400">
			{#if !$connected}
				Connecting...
			{:else}
				Connected
			{/if}
		</span>
		<button
			onclick={handleNewChat}
			class="text-xs text-slate-500 hover:text-indigo-400 transition-colors"
		>
			+ New chat
		</button>
	</div>

	<!-- Messages -->
	<div bind:this={messagesContainer} class="flex-1 overflow-y-auto px-4 py-4">
		{#if !$historyLoaded}
			<div class="flex justify-center py-8">
				<p class="text-sm text-slate-500">Loading history...</p>
			</div>
		{:else if $messages.length === 0 && $connected}
			<div class="flex justify-center py-8">
				<p class="text-sm text-slate-500">Start a conversation with Mirror</p>
			</div>
		{/if}

		{#each $messages as message (message.timestamp + message.content.slice(0, 20))}
			<MessageBubble {message} />
		{/each}

		{#if $isTyping}
			<TypingIndicator />
		{/if}
	</div>

	<!-- Flow widgets -->
	{#if showFlowWidget && lastFlowPrompt}
		{#if lastFlowPrompt.input_type === 'choice' && lastFlowPrompt.options}
			<QuickReply options={lastFlowPrompt.options} onSelect={handleQuickReply} />
		{:else if lastFlowPrompt.input_type === 'slider'}
			<EnergySlider
				prompt={lastFlowPrompt.prompt}
				min={lastFlowPrompt.min_val ?? 1}
				max={lastFlowPrompt.max_val ?? 10}
				onSubmit={handleSlider}
			/>
		{/if}
	{/if}

	<!-- Input -->
	<div class="border-t border-[var(--color-border)] p-3">
		<div class="flex items-end gap-2 max-w-3xl mx-auto">
			<textarea
				bind:value={inputText}
				onkeydown={handleKeydown}
				placeholder="Type a message..."
				rows={1}
				class="flex-1 bg-[var(--color-surface-lighter)] text-[var(--color-text)] rounded-xl px-4 py-2.5
					text-sm resize-none border border-[var(--color-border)] focus:border-indigo-500
					focus:outline-none placeholder-slate-500"
			></textarea>
			<button
				onclick={handleSend}
				disabled={!inputText.trim() || !$connected}
				class="bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed
					text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-colors"
			>
				Send
			</button>
		</div>
	</div>
</div>
