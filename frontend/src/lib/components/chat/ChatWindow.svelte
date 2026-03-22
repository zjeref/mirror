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

	onMount(() => {
		if (!$historyLoaded) {
			chat.loadHistory().then(() => chat.connect());
		} else {
			chat.connect();
		}
		return () => chat.pause();
	});

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
		if (confirm('Start a new conversation? Your chat history is saved.')) {
			chat.startNewConversation();
		}
	}

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

<div class="flex flex-col h-full chat-gradient">
	<!-- Header -->
	<header class="flex justify-between items-center px-8 py-4 bg-[var(--color-surface)]/70 backdrop-blur-xl border-b border-[var(--color-outline-variant)]/10">
		<div class="flex items-center gap-3">
			<span class="material-symbols-outlined text-[var(--color-tertiary)]">flare</span>
			<span class="text-xl font-bold bg-gradient-to-br from-indigo-300 to-indigo-500 bg-clip-text text-transparent tracking-tight">Mirror</span>
		</div>
		<div class="flex items-center gap-4">
			<div class="flex items-center gap-2 bg-[var(--color-surface-low)] px-3 py-1.5 rounded-full border border-[var(--color-outline-variant)]/10">
				<span class="w-2 h-2 rounded-full {$connected ? 'bg-[var(--color-tertiary)] ember-glow animate-pulse' : 'bg-[var(--color-outline)]'}"></span>
				<span class="text-xs font-medium text-[var(--color-on-surface-variant)]">{$connected ? 'Connected' : 'Connecting...'}</span>
			</div>
			<button
				onclick={handleNewChat}
				class="text-xs text-[var(--color-outline)] hover:text-[var(--color-primary)] transition-colors flex items-center gap-1"
			>
				<span class="material-symbols-outlined text-sm">add</span>
				New chat
			</button>
		</div>
	</header>

	<!-- Messages -->
	<section bind:this={messagesContainer} class="flex-1 overflow-y-auto px-6 md:px-24 py-8 flex flex-col gap-6">
		{#if !$historyLoaded}
			<div class="flex justify-center py-12">
				<div class="flex gap-1.5">
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce"></div>
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
					<div class="w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
				</div>
			</div>
		{:else if $messages.length === 0 && $connected}
			<div class="flex flex-col items-center justify-center py-16 gap-4">
				<span class="material-symbols-outlined filled text-5xl text-[var(--color-primary)]/30">auto_awesome</span>
				<p class="text-[var(--color-on-surface-variant)]/60 text-sm">Start a conversation with Mirror</p>
				<div class="flex gap-2 mt-2">
					{#each ['How am I doing?', 'I need to vent', 'Help me focus'] as suggestion}
						<button
							onclick={() => { chat.sendMessage(suggestion); }}
							class="text-xs px-3 py-1.5 rounded-full border border-[var(--color-outline-variant)]/20 text-[var(--color-on-surface-variant)] hover:border-[var(--color-primary)]/40 hover:text-[var(--color-primary)] transition-all"
						>
							{suggestion}
						</button>
					{/each}
				</div>
			</div>
		{/if}

		{#each $messages as message (message.timestamp + message.content.slice(0, 20))}
			<MessageBubble {message} />
		{/each}

		{#if $isTyping}
			<TypingIndicator />
		{/if}
	</section>

	<!-- Flow widgets -->
	{#if showFlowWidget && lastFlowPrompt}
		<div class="px-6 md:px-24 pb-2">
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
		</div>
	{/if}

	<!-- Input -->
	<footer class="px-6 md:px-24 pb-8 pt-4 bg-gradient-to-t from-[var(--color-surface)] to-transparent">
		<div class="relative group">
			<div class="absolute inset-0 bg-[var(--color-tertiary)]/5 blur-xl rounded-full opacity-0 group-focus-within:opacity-100 transition-opacity duration-500"></div>
			<div class="relative flex items-center bg-[var(--color-surface-low)] border-2 border-[var(--color-tertiary)]/20 focus-within:border-[var(--color-tertiary)]/50 transition-all duration-300 rounded-full px-6 py-3">
				<input
					bind:value={inputText}
					onkeydown={handleKeydown}
					placeholder="Share your thoughts..."
					class="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none text-[var(--color-on-surface)] placeholder-[var(--color-outline)]/50 px-2 text-base"
				/>
				<button
					onclick={handleSend}
					disabled={!inputText.trim() || !$connected}
					class="bg-[var(--color-tertiary)] text-[#442c00] w-10 h-10 rounded-full flex items-center justify-center
						hover:scale-105 active:scale-95 transition-all shadow-lg shadow-[var(--color-tertiary)]/20
						disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
				>
					<span class="material-symbols-outlined filled text-xl">send</span>
				</button>
			</div>
		</div>
		<p class="text-center mt-4 text-[10px] text-[var(--color-on-surface-variant)]/30 tracking-widest uppercase">
			Your private sanctuary
		</p>
	</footer>
</div>
