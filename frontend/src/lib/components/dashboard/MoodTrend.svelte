<script lang="ts">
	interface Props {
		dataPoints: { date: string; score: number }[];
		trend: string | null;
	}

	let { dataPoints, trend }: Props = $props();

	const maxScore = 10;
	const height = 120;
	const width = 400;

	const points = $derived(
		dataPoints.map((dp, i) => ({
			x: (i / Math.max(dataPoints.length - 1, 1)) * width,
			y: height - (dp.score / maxScore) * height,
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
			? `${pathD} L ${width},${height} L 0,${height} Z`
			: ''
	);

	const trendColor = $derived(
		trend === 'improving' ? 'text-green-400' : trend === 'declining' ? 'text-rose-400' : 'text-slate-400'
	);

	const trendIcon = $derived(
		trend === 'improving' ? '↑' : trend === 'declining' ? '↓' : '→'
	);
</script>

<div>
	<div class="flex items-center justify-between mb-3">
		<h3 class="text-sm font-medium text-slate-300">Mood Trend</h3>
		{#if trend}
			<span class="text-xs {trendColor}">{trendIcon} {trend}</span>
		{/if}
	</div>

	{#if points.length > 1}
		<svg viewBox="0 0 {width} {height}" class="w-full h-28">
			<!-- Area fill -->
			<path d={areaD} fill="url(#moodGradient)" opacity="0.3" />
			<!-- Line -->
			<path d={pathD} fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" />
			<!-- Dots -->
			{#each points as point}
				<circle cx={point.x} cy={point.y} r="3" fill="#818cf8" />
			{/each}

			<defs>
				<linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="#818cf8" />
					<stop offset="100%" stop-color="transparent" />
				</linearGradient>
			</defs>
		</svg>
	{:else}
		<div class="h-28 flex items-center justify-center text-sm text-slate-500">
			Not enough data yet. Check in daily to see trends.
		</div>
	{/if}
</div>
