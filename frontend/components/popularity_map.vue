<template>
  <canvas ref="canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps<{ songId: number; startDate?: string; endDate?: string }>()
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

async function render() {
  const params = new URLSearchParams()
  if (props.startDate) params.append('start_date', props.startDate)
  if (props.endDate) params.append('end_date', props.endDate)
  const query = params.toString()
  const resp = await fetch(
    `/music/metrics/songs/${props.songId}/popularity${query ? `?${query}` : ''}`,
  )
  const data = await resp.json()
  const breakdown = data.breakdown || {}
  const labels: string[] = []
  const values: number[] = []
  for (const [region, platforms] of Object.entries(breakdown)) {
    const total = Object.values(platforms as Record<string, number>)
      .map(v => Number(v))
      .reduce((a, b) => a + b, 0)
    labels.push(region)
    values.push(total)
  }
  if (canvas.value) {
    if (chart) chart.destroy()
    chart = new Chart(canvas.value, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Popularity', data: values }],
      },
    })
  }
}

onMounted(render)
watch(() => [props.songId, props.startDate, props.endDate], render)
</script>
