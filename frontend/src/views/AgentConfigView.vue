<template>
  <div class="agent-config">
    <h2>配置编程智能体</h2>
    <div class="form-group">
      <label>智能体名称</label>
      <input v-model="name" placeholder="如：QMT编程助手" />
    </div>
    <div class="form-group">
      <label>选择Skills群</label>
      <div v-for="g in skillGroups" :key="g.id" class="skill-item" @click="toggleGroup(g.id)" :class="{ selected: selectedGroups.includes(g.id) }">
        <span>{{ g.name }}</span>
        <span class="count">{{ g.skill_count }}个Skills</span>
      </div>
      <p v-if="!skillGroups.length" class="empty">暂无Skills群，请先上传PDF</p>
    </div>
    <div class="form-group">
      <label>模型类型</label>
      <select v-model="modelProvider">
        <option value="modelscope">魔搭社区</option>
        <option value="openai">OpenAI</option>
        <option value="local">本地模型</option>
      </select>
    </div>
    <div class="form-group">
      <label>模型ID</label>
      <input v-model="modelId" placeholder="如：Qwen/Qwen2.5-Coder-32B-Instruct" />
    </div>
    <div class="form-group">
      <label>API Key</label>
      <input v-model="apiKey" type="password" placeholder="输入API Key" />
    </div>
    <div class="form-group">
      <label>Base URL (可选)</label>
      <input v-model="baseUrl" placeholder="自定义API端点" />
    </div>
    <button @click="createAgent" :disabled="!canCreate">创建智能体</button>

    <div v-if="agents.length" class="agent-list">
      <h3>已创建的智能体</h3>
      <div v-for="a in agents" :key="a.id" class="agent-card" @click="$router.push(`/chat/${a.id}`)">
        <strong>{{ a.name }}</strong>
        <span>{{ a.model_provider }} / {{ a.model_id }}</span>
        <span :class="a.is_active ? 'active' : 'inactive'">{{ a.is_active ? '活跃' : '停用' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/http'

const name = ref('')
const modelProvider = ref('modelscope')
const modelId = ref('')
const apiKey = ref('')
const baseUrl = ref('')
const selectedGroups = ref<string[]>([])
const skillGroups = ref<any[]>([])
const agents = ref<any[]>([])

const canCreate = computed(() => name.value && modelId.value && selectedGroups.value.length > 0)

function toggleGroup(id: string) {
  const idx = selectedGroups.value.indexOf(id)
  if (idx >= 0) selectedGroups.value.splice(idx, 1)
  else selectedGroups.value.push(id)
}

async function loadSkillGroups() {
  try {
    const res = await http.get('/agent/skill-groups')
    skillGroups.value = res.data
  } catch {}
}

async function loadAgents() {
  try {
    const res = await http.get('/agent/list')
    agents.value = res.data
  } catch {}
}

async function createAgent() {
  try {
    await http.post('/agent/create', {
      name: name.value,
      model_config: { provider: modelProvider.value, model_id: modelId.value, api_key: apiKey.value, base_url: baseUrl.value },
      skill_group_ids: selectedGroups.value,
    })
    name.value = ''
    await loadAgents()
  } catch (e: any) {
    alert(e.response?.data?.detail || '创建失败')
  }
}

onMounted(() => { loadSkillGroups(); loadAgents() })
</script>

<style scoped>
.agent-config h2 { margin-bottom: 1rem; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: .3rem; font-size: 14px; font-weight: 500; }
input, select { width: 100%; max-width: 400px; padding: .5rem; border: 1px solid #ddd; border-radius: 4px; }
.skill-item { padding: .5rem; border: 1px solid #e2e8f0; border-radius: 4px; margin-bottom: .3rem; cursor: pointer; display: flex; justify-content: space-between; }
.skill-item.selected { border-color: #4f46e5; background: #eef2ff; }
.count { font-size: 12px; color: #64748b; }
.empty { color: #94a3b8; font-size: 13px; }
button { padding: .6rem 1.5rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: .6; }
.agent-list { margin-top: 2rem; }
.agent-card { padding: .8rem; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: .5rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.agent-card:hover { background: #f1f5f9; }
.active { color: #22c55e; } .inactive { color: #94a3b8; }
</style>
