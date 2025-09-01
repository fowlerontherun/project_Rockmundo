<template>
  <div class="setlist-editor">
    <div class="controls">
      <textarea
        v-model="currentSetlist"
        placeholder="Enter setlist JSON"
        @dragover.prevent
        @drop="onDrop"
      ></textarea>
      <div class="actions">
        <select v-model="objective">
          <option value="crowd_energy">Crowd Energy</option>
          <option value="fame_gain">Fame Gain</option>
        </select>
        <button @click="getRecommendation">Get Recommendation</button>
        <button @click="submitRevision">Submit Revision</button>
      </div>
    </div>

    <div v-if="recommendation.length" class="recommendation">
      <h3>Recommended Order</h3>
      <ul draggable="true" @dragstart="onDragStart">
        <li v-for="(song, i) in recommendation" :key="i">{{ song }}</li>
      </ul>
    </div>

    <ul>
      <li v-for="rev in revisions" :key="rev.id">
        <pre>{{ rev.setlist }}</pre>
        <span>{{ rev.author }} - {{ rev.created_at }}</span>
        <button v-if="!rev.approved" @click="approve(rev.id)">Approve</button>
        <span v-else>Approved</span>
      </li>
    </ul>

    <div class="comments">
      <h3>Comments</h3>
      <textarea v-model="comment" placeholder="Add a comment"></textarea>
      <button @click="addComment">Add Comment</button>
      <ul>
        <li v-for="(c, i) in comments" :key="i">{{ c }}</li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    setlistId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      currentSetlist: '',
      revisions: [],
      comment: '',
      comments: [],
      poller: null,
      recommendation: [],
      objective: 'crowd_energy'
    }
  },
  created() {
    this.fetchRevisions()
    this.poller = setInterval(this.fetchRevisions, 5000)
  },
  beforeUnmount() {
    clearInterval(this.poller)
  },
  methods: {
    async fetchRevisions() {
      const res = await fetch(`/api/setlists/${this.setlistId}/revisions`)
      this.revisions = await res.json()
    },
    async submitRevision() {
      if (!this.currentSetlist) return
      await fetch(`/api/setlists/${this.setlistId}/revisions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ setlist: JSON.parse(this.currentSetlist), author: 'anonymous' })
      })
      if (this.recommendation.length) {
        await fetch('/api/setlists/recommend/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected: JSON.parse(this.currentSetlist),
            recommended: this.recommendation,
            objective: this.objective
          })
        })
      }
      this.currentSetlist = ''
      this.fetchRevisions()
    },
    async approve(id) {
      await fetch(`/api/setlists/${this.setlistId}/revisions/${id}/approve`, { method: 'POST' })
      this.fetchRevisions()
    },
    addComment() {
      if (this.comment) {
        this.comments.push(this.comment)
        this.comment = ''
      }
    },
    async getRecommendation() {
      const songs = this.currentSetlist ? JSON.parse(this.currentSetlist) : []
      const res = await fetch('/api/setlists/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ songs, objective: this.objective })
      })
      const data = await res.json()
      this.recommendation = data.recommended_order || []
    },
    onDragStart(e) {
      e.dataTransfer.setData('text/plain', JSON.stringify(this.recommendation))
    },
    onDrop(e) {
      const data = e.dataTransfer.getData('text/plain')
      if (data) {
        this.currentSetlist = data
      }
    }
  }
}
</script>

<style scoped>
.setlist-editor textarea {
  width: 100%;
  min-height: 100px;
  margin-bottom: 0.5rem;
}

.recommendation ul {
  list-style: none;
  padding: 0;
}

.recommendation li {
  cursor: move;
}
</style>
