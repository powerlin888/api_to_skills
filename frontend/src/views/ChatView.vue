<template>
  <div class="chat-view">
    <h2>对话 - {{ agentName }}</h2>
    <div class="messages" ref="messagesRef">
      <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
        <div class="bubble" v-html="renderMarkdown(msg.content)"></div>
      </div>
    </div>
    <div v-if="metrics" class="metrics">
      模型调用:{{ metrics.model_calls }} | 输入Token:{{ metrics.input_tokens }} | 输出Token:{{ metrics.output_tokens }} | 耗时:{{ metrics.latency_ms }}ms
    </div>
    <div class="input-area">
      <textarea v-model="input" @keydown.enter.exact.prevent="send" :disabled="streaming" placeholder="输入消息..." rows="2"></textarea>
      <button @click="send" :disabled="streaming || !input.trim()">{{ streaming ? '回复中...' : '发送' }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import http from '@/api/http'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()
const route = useRoute()
const agentId = route.params.agentId as string
const agentName = ref('')
const messages = ref<{ role: string; content: string }[]>([])
const input = ref('')
const streaming = ref(false)
const metrics = ref<any>(null)
const messagesRef = ref<HTMLElement>()

function renderMarkdown(content: string) { return md.render(content) }

async function send() {
  if (!input.value.trim() || streaming.value) return
  const msg = input.value.trim()
  messages.value.push({ role: 'user', content: msg })
  input.value = ''
  streaming.value = true
  metrics.value = null
  messages.value.push({ role: 'assistant', content: '' })
  const aiIdx = messages.value.length - 1

  try {
    const res = await fetch(`/api/chat/${agentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      body: JSON.stringify({ message: msg }),
    })
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) throw new Error('无响应流')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'token') {
            messages.value[aiIdx].content += event.content
          } else if (event.type === 'done') {
            metrics.value = event
          } else if (event.type === 'error') {
            messages.value[aiIdx].content += `\n\n[错误] ${event.content}`
          }
        } catch {}
      }
      await nextTick()
      messagesRef.value?.scrollTo({ top: messagesRef.value.scrollHeight })
    }
  } catch {
    messages.value[aiIdx].content = '[连接失败，请重试]'
  } finally {
    streaming.value = false
  }
}

onMounted(async () => {
  try {
    const res = await http.get(`/agent/${agentId}`)
    agentName.value = res.data.name
  } catch {}
})
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: calc(100vh - 4rem); }
.messages { flex: 1; overflow-y: auto; padding: 1rem; }
.msg { margin-bottom: 1rem; }
.msg.user { text-align: right; }
.bubble { display: inline-block; max-width: 70%; padding: .8rem; border-radius: 8px; text-align: left; }
.msg.user .bubble { background: #4f46e5; color: #fff; }
.msg.assistant .bubble { background: #fff; border: 1px solid #e2e8f0; }
.metrics { padding: .5rem 1rem; font-size: 12px; color: #64748b; background: #f1f5f9; }
.input-area { display: flex; gap: .5rem; padding: 1rem; border-top: 1px solid #e2e8f0; }
textarea { flex: 1; padding: .5rem; border: 1px solid #ddd; border-radius: 4px; resize: none; }
button { padding: .5rem 1rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: .6; }
</style>
