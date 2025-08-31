<template>
  <canvas ref="canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'

const props = defineProps<{ songId: number }>()
const canvas = ref<HTMLCanvasElement | null>(null)

onMounted(async () => {
  const resp = await fetch(`/music/metrics/songs/${props.songId}/popularity`)
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
    new Chart(canvas.value, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Popularity', data: values }],
      },
    })
  }
})
</script>
