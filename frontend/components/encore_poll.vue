<template>
  <div class="encore-poll">
    <div class="options">
      <button
        v-for="song in songs"
        :key="song.id"
        @click="vote(song.id)"
      >
        {{ song.title }}
      </button>
    </div>
    <ul class="leaderboard">
      <li v-for="item in leaderboard" :key="item.song">
        {{ item.song }} - {{ item.votes }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    pollId: { type: String, required: true },
    songs: { type: Array, required: true } // [{id, title}]
  },
  data() {
    return {
      ws: null,
      leaderboard: []
    }
  },
  mounted() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    this.ws = new WebSocket(`${protocol}://${window.location.host}/encore/ws/${this.pollId}`)
    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'leaderboard') {
          this.leaderboard = Object.entries(msg.votes).map(([song, votes]) => ({ song, votes }))
        }
      } catch (e) {
        // ignore malformed messages
      }
    }
  },
  beforeUnmount() {
    if (this.ws) this.ws.close()
  },
  methods: {
    vote(songId) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ vote: songId }))
      }
    }
  }
}
</script>

<style scoped>
.encore-poll button {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
