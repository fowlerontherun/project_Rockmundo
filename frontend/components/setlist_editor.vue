<template>
  <div class="setlist-editor">
    <textarea v-model="currentSetlist" placeholder="Enter setlist JSON"></textarea>
    <button @click="submitRevision">Submit Revision</button>

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
      comments: []
    }
  },
  created() {
    this.fetchRevisions()
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
</style>
