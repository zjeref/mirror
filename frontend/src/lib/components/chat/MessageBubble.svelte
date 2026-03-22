<script lang="ts">
	import type { ChatMessage } from '$lib/stores/chat';

	interface Props {
		message: ChatMessage;
	}

	let { message }: Props = $props();

	const isUser = $derived(message.role === 'user');

	function formatContent(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/\n/g, '<br>')
			.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
			.replace(/_(.*?)_/g, '<em>$1</em>');
	}
</script>

<div class="flex flex-col {isUser ? 'items-end' : 'items-start'} gap-1.5 max-w-[80%] {isUser ? 'self-end' : ''}">
	{#if !isUser}
		<div class="flex items-center gap-2 px-2">
			<span class="text-[10px] font-semibold text-[var(--color-tertiary)]/70 uppercase tracking-widest">Mirror</span>
		</div>
	{/if}

	<div class="{isUser
		? 'bg-[var(--color-primary-container)] text-[var(--color-on-primary-container)] rounded-2xl rounded-tr-sm shadow-lg shadow-[var(--color-primary-container)]/20'
		: 'bg-[var(--color-surface-low)]/70 backdrop-blur-md text-[var(--color-on-surface)] rounded-2xl rounded-tl-sm border border-[var(--color-outline-variant)]/5'} px-5 py-3.5"
	>
		<p class="text-[15px] leading-relaxed">
			{@html formatContent(message.content)}
		</p>
	</div>
</div>
