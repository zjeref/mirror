<script lang="ts">
	interface Props {
		dataPoints: { date: string; score: number }[];
		trend: string | null;
	}

	let { dataPoints, trend }: Props = $props();

	const maxScore = 10;
	const height = 140;
	const width = 400;
	const padding = { left: 30, right: 10, top: 10, bottom: 25 };
	const plotW = width - padding.left - padding.right;
	const plotH = height - padding.top - padding.bottom;

	const points = $derived(
		dataPoints.map((dp, i) => ({
			x: padding.left + (i / Math.max(dataPoints.length - 1, 1)) * plotW,
			y: padding.top + plotH - (dp.score / maxScore) * plotH,
			score: dp.score,
			date: dp.date,
		}))
	);

	const pathD = $derived(
		points.length > 1
			? `M ${points.map((p) => `${p.x},${p.y}`).join(' L ')}`
			: ''
	);

	const areaD = $derived(
		points.length > 1
			? `${pathD} L ${points[points.length - 1].x},${padding.top + plotH} L ${padding.left},${padding.top + plotH} Z`
			: ''
	);

	const trendColor = $derived(
		trend === 'improving' ? 'text-emerald-400' : trend === 'declining' ? 'text-rose-400' : 'text-[var(--color-on-surface-variant)]'
	);

	const trendIcon = $derived(
		trend === 'improving' ? '↑' : trend === 'declining' ? '↓' : '→'
	);
</script>

<div>
	<div class="flex items-center justify-between mb-3">
		<h3 class="text-sm font-semibold text-[var(--color-on-surface)]">Mood Trend</h3>
		{#if trend}
			<span class="text-xs font-medium {trendColor}">{trendIcon} {trend}</span>
		{/if}
	</div>

	{#if points.length > 1}
		<svg viewBox="0 0 {width} {height}" class="w-full h-36">
			<!-- Y axis labels -->
			{#each [2, 5, 8] as label}
				<text x={padding.left - 8} y={padding.top + plotH - (label / maxScore) * plotH + 4}
					fill="var(--color-outline)" font-size="9" text-anchor="end">{label}</text>
				<line x1={padding.left} y1={padding.top + plotH - (label / maxScore) * plotH}
					x2={width - padding.right} y2={padding.top + plotH - (label / maxScore) * plotH}
					stroke="var(--color-outline-variant)" stroke-width="0.5" stroke-dasharray="4,4" opacity="0.3" />
			{/each}

			<!-- Area fill -->
			<path d={areaD} fill="url(#moodGradientWarm)" opacity="0.4" />
			<!-- Line -->
			<path d={pathD} fill="none" stroke="var(--color-tertiary)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
			<!-- Dots -->
			{#each points as point}
				<circle cx={point.x} cy={point.y} r="3.5" fill="var(--color-tertiary)" />
				<circle cx={point.x} cy={point.y} r="6" fill="var(--color-tertiary)" opacity="0.15" />
			{/each}

			<!-- X axis dates (first + last) -->
			{#if points.length >= 2}
				<text x={points[0].x} y={height - 4} fill="var(--color-outline)" font-size="9" text-anchor="start">
					{new Date(points[0].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
				</text>
				<text x={points[points.length - 1].x} y={height - 4} fill="var(--color-outline)" font-size="9" text-anchor="end">
					{new Date(points[points.length - 1].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
				</text>
			{/if}

			<defs>
				<linearGradient id="moodGradientWarm" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="#edbf7c" />
					<stop offset="100%" stop-color="transparent" />
				</linearGradient>
			</defs>
		</svg>
	{:else}
		<div class="h-36 flex flex-col items-center justify-center gap-2">
			<span class="material-symbols-outlined text-3xl text-[var(--color-outline)]/30">show_chart</span>
			<p class="text-sm text-[var(--color-outline)]">Chat with Mirror to see your mood trends</p>
		</div>
	{/if}
</div>
