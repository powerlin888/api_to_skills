<template>
  <div class="community">
    <h2>社区</h2>
    <div class="check-in">
      <button @click="checkIn" :disabled="checkedIn">{{ checkedIn ? '今日已签到' : '签到' }}</button>
      <span v-if="checkInMsg" :class="checkInSuccess ? 'success' : 'info'">{{ checkInMsg }}</span>
    </div>
    <div class="post-editor">
      <input v-model="postTitle" placeholder="帖子标题" maxlength="200" />
      <textarea v-model="postContent" placeholder="帖子内容" maxlength="10000" rows="3"></textarea>
      <button @click="createPost" :disabled="!postTitle.trim() || !postContent.trim()">发帖</button>
    </div>
    <div class="post-list">
      <div v-for="post in posts" :key="post.id" class="post-card">
        <h3>{{ post.title }}</h3>
        <p class="meta">{{ post.author_nickname }} · {{ formatDate(post.created_at) }}</p>
        <p>{{ post.content }}</p>
        <div class="actions">
          <button @click="toggleLike(post.id)">{{ post.like_count }} 赞</button>
          <span>{{ post.comment_count }} 评论</span>
        </div>
        <div class="comments">
          <input v-model="commentInput[post.id]" placeholder="写评论" />
          <button @click="addComment(post.id)">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import http from '@/api/http'

const checkedIn = ref(false)
const checkInMsg = ref('')
const checkInSuccess = ref(false)
const postTitle = ref('')
const postContent = ref('')
const posts = ref<any[]>([])
const commentInput = reactive<Record<string, string>>({})

function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }

async function checkIn() {
  try {
    const res = await http.post('/community/check-in')
    checkInSuccess.value = res.data.success
    checkInMsg.value = res.data.message
    if (res.data.success) checkedIn.value = true
  } catch (e: any) {
    checkInMsg.value = e.response?.data?.detail || '签到失败'
  }
}

async function loadPosts() {
  try {
    const res = await http.get('/community/posts')
    posts.value = res.data.items || res.data
  } catch {}
}

async function createPost() {
  try {
    await http.post('/community/posts', { title: postTitle.value, content: postContent.value })
    postTitle.value = ''
    postContent.value = ''
    await loadPosts()
  } catch (e: any) {
    alert(e.response?.data?.detail || '发帖失败')
  }
}

async function toggleLike(postId: string) {
  try {
    await http.post(`/community/posts/${postId}/like`)
    await loadPosts()
  } catch {}
}

async function addComment(postId: string) {
  const content = commentInput[postId]
  if (!content?.trim()) return
  try {
    await http.post(`/community/posts/${postId}/comments`, { content })
    commentInput[postId] = ''
    await loadPosts()
  } catch {}
}

onMounted(() => { checkIn(); loadPosts() })
</script>

<style scoped>
.community h2 { margin-bottom: 1rem; }
.check-in { margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem; }
.check-in button { padding: .4rem 1rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.check-in button:disabled { opacity: .6; }
.success { color: #22c55e; } .info { color: #3b82f6; }
.post-editor { background: #fff; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; }
.post-editor input, .post-editor textarea { width: 100%; padding: .4rem; margin-bottom: .5rem; border: 1px solid #ddd; border-radius: 4px; }
.post-editor button { padding: .4rem 1rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.post-list { display: flex; flex-direction: column; gap: 1rem; }
.post-card { background: #fff; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; }
.meta { font-size: 13px; color: #64748b; }
.actions { margin-top: .5rem; display: flex; gap: 1rem; }
.actions button { background: none; border: 1px solid #ddd; padding: .2rem .6rem; border-radius: 4px; cursor: pointer; font-size: 13px; }
.comments { margin-top: .5rem; display: flex; gap: .5rem; }
.comments input { flex: 1; padding: .3rem; border: 1px solid #ddd; border-radius: 4px; }
.comments button { padding: .3rem .8rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
</style>
