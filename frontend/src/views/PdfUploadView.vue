<template>
  <div class="pdf-upload">
    <h2>上传编程指南</h2>
    <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop" @click="triggerInput" :class="{ active: dragging }">
      <input ref="fileInput" type="file" accept=".pdf" @change="handleFileSelect" hidden />
      <p>拖拽PDF文件到此处，或点击选择文件</p>
      <p class="hint">支持PDF格式，最大100MB</p>
    </div>

    <!-- 去重确认弹窗 -->
    <div v-if="dedupDialog.visible" class="dedup-overlay">
      <div class="dedup-dialog">
        <h3>发现相似指南</h3>
        <p>已存在相似指南：<strong>{{ dedupDialog.guideName }}</strong></p>
        <p>相似度：<strong>{{ (dedupDialog.similarity * 100).toFixed(1) }}%</strong></p>
        <div class="dedup-actions">
          <button class="btn-continue" @click="dedupContinue">继续生成新Skills</button>
          <button class="btn-cancel" @click="dedupCancel">使用已有Skills</button>
        </div>
      </div>
    </div>

    <div v-if="tasks.length" class="task-list">
      <div v-for="task in tasks" :key="task.id" class="task-item">
        <span>{{ task.id.slice(0, 8) }}</span>
        <span :class="'status-' + task.status">{{ statusLabel(task.status) }}</span>
        <span v-if="task.status === 'duplicate'" class="dup-badge">
          已关联已有指南
          <router-link v-if="task.dedup_info?.existing_group_id"
            :to="`/agent-config`" class="dup-link">查看Skills群 →</router-link>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import http from '@/api/http'

const fileInput = ref<HTMLInputElement>()
const dragging = ref(false)
const tasks = ref<any[]>([])
const pollingTimers = ref<Record<string, number>>({})

const dedupDialog = reactive({
  visible: false, taskId: '', guideName: '', similarity: 0, groupId: ''
})

function triggerInput() { fileInput.value?.click() }

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: '等待中', parsing: '解析PDF', dedup_check: '去重检查',
    analyzing: 'LLM分析', generating: '生成Skills', validating: '验证',
    completed: '完成', failed: '失败', duplicate: '重复'
  }
  return labels[status] || status
}

async function handleFileSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) await uploadFile(file)
}

async function handleDrop(e: DragEvent) {
  const file = e.dataTransfer?.files[0]
  if (file && file.name.endsWith('.pdf')) await uploadFile(file)
}

async function uploadFile(file: File) {
  const form = new FormData()
  form.append('file', file)
  console.log('[PDF上传] 开始上传:', file.name, '大小:', file.size)
  try {
    const res = await http.post('/pdf/upload', form)
    console.log('[PDF上传] 上传响应:', res.data)
    const taskData = { ...res.data, id: res.data.task_id }
    tasks.value.unshift(taskData)
    startPolling(res.data.task_id)
  } catch (e: any) {
    console.error('[PDF上传] 上传失败:', e.response?.status, e.response?.data || e.message)
    alert(e.response?.data?.detail || `上传失败: ${e.response?.status || e.message}`)
  }
}

function startPolling(taskId: string) {
  const timer = setInterval(async () => {
    try {
      const res = await http.get(`/pdf/tasks/${taskId}`)
      const task = res.data
      console.log('[PDF轮询] 任务状态:', taskId.slice(0, 8), task.status, task)
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx >= 0) {
        tasks.value[idx] = { ...tasks.value[idx], ...task, id: taskId }
      } else {
        console.warn('[PDF轮询] 未找到本地任务:', taskId)
      }
      if (task.status === 'dedup_check' && task.dedup_info?.match_type === 'similar') {
        clearInterval(timer)
        dedupDialog.visible = true
        dedupDialog.taskId = taskId
        dedupDialog.guideName = task.dedup_info.similar_guide_name || '未知指南'
        dedupDialog.similarity = task.dedup_info.similarity || 0
        dedupDialog.groupId = task.dedup_info.existing_group_id || ''
      }
      if (['completed', 'failed', 'duplicate'].includes(task.status)) {
        clearInterval(timer)
      }
    } catch (e: any) {
      console.error('[PDF轮询] 轮询失败:', e.response?.status, e.response?.data || e.message)
      clearInterval(timer)
    }
  }, 2000)
  pollingTimers.value[taskId] = timer as any
}

async function dedupContinue() {
  try {
    await http.post(`/pdf/tasks/${dedupDialog.taskId}/confirm-dedup`, { action: 'continue' })
    dedupDialog.visible = false
    startPolling(dedupDialog.taskId)
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function dedupCancel() {
  try {
    await http.post(`/pdf/tasks/${dedupDialog.taskId}/confirm-dedup`, { action: 'cancel' })
    dedupDialog.visible = false
    const idx = tasks.value.findIndex(t => t.id === dedupDialog.taskId)
    if (idx >= 0) {
      tasks.value[idx] = { ...tasks.value[idx], status: 'duplicate' }
    }
  } catch (e: any) {
    alert(e.response?.data?.detail || '操作失败')
  }
}
</script>

<style scoped>
.pdf-upload h2 { margin-bottom: 1rem; }
.upload-area { border: 2px dashed #cbd5e1; border-radius: 8px; padding: 3rem; text-align: center; cursor: pointer; transition: all .2s; }
.upload-area:hover, .upload-area.active { border-color: #4f46e5; background: #f1f5f9; }
.hint { font-size: 13px; color: #94a3b8; margin-top: .5rem; }
.task-list { margin-top: 1.5rem; }
.task-item { display: flex; align-items: center; gap: .8rem; padding: .5rem; border-bottom: 1px solid #e2e8f0; }
.status-completed { color: #22c55e; } .status-failed { color: #ef4444; }
.status-pending, .status-parsing, .status-analyzing, .status-generating, .status-validating { color: #3b82f6; }
.status-dedup_check { color: #f59e0b; } .status-duplicate { color: #8b5cf6; }
.dup-badge { font-size: 12px; color: #8b5cf6; }
.dup-link { color: #4f46e5; text-decoration: underline; cursor: pointer; margin-left: .5rem; font-size: 12px; }
.dedup-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dedup-dialog { background: #fff; padding: 2rem; border-radius: 8px; min-width: 360px; }
.dedup-dialog h3 { margin-bottom: 1rem; }
.dedup-dialog p { margin-bottom: .5rem; }
.dedup-actions { display: flex; gap: 1rem; margin-top: 1.5rem; }
.btn-continue { padding: .5rem 1rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.btn-cancel { padding: .5rem 1rem; background: #8b5cf6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
</style>
