<template>
  <ul>
    <li v-for="evt in events" :key="evt.id">
      {{ new Date(evt.created_at).toLocaleDateString() }} - {{ formatEvent(evt) }}
    </li>
  </ul>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

interface TimelineEvent {
  id: number
  source: string
  boost: number
  details: string
  created_at: string
}

const props = defineProps<{ songId: number }>()
const events = ref<TimelineEvent[]>([])

function formatEvent(e: TimelineEvent): string {
  if (e.source.startsWith('legacy_')) {
    return `Became ${e.source.replace('legacy_', '')}`
  }
  if (e.source === 'remaster_release') {
    return 'Remaster released'
  }
  if (e.source === 'retired_royalty') {
    return 'Residual royalties'
  }
  return e.source
}

async function load() {
  const resp = await fetch(`/song-popularity/events?song_id=${props.songId}`)
  const data = await resp.json()
  events.value = data.events || []
}

onMounted(load)
watch(() => props.songId, load)
</script>
