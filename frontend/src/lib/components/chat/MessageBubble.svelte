<script lang="ts">
	import type { ChatMessage } from '$lib/stores/chat';

	interface Props {
		message: ChatMessage;
	}

	let { message }: Props = $props();

	const isUser = $derived(message.role === 'user');
</script>

<div class="flex {isUser ? 'justify-end' : 'justify-start'} mb-3">
	<div
		class="max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
		{isUser
			? 'bg-indigo-500 text-white rounded-br-md'
			: 'bg-[var(--color-surface-lighter)] text-[var(--color-text)] rounded-bl-md'}"
	>
		{@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/_(.*?)_/g, '<em>$1</em>').replace(/> (.*?)(<br>|$)/g, '<blockquote class="border-l-2 border-indigo-400 pl-3 my-1 text-slate-300">$1</blockquote>')}
	</div>
</div>
