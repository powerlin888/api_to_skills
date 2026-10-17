<template>
  <div class="model-config">
    <h2>模型配置</h2>
    <div v-for="p in providers" :key="p.id" class="provider-card">
      <h3>{{ p.name }}</h3>
      <div class="form-group">
        <label>Base URL</label>
        <input v-model="p.baseUrl" :placeholder="p.defaultUrl" />
      </div>
      <div class="form-group">
        <label>API Key</label>
        <input v-model="p.apiKey" type="password" placeholder="输入API Key" />
      </div>
      <div class="form-group">
        <label>模型ID</label>
        <input v-model="p.modelId" placeholder="模型名称" />
      </div>
      <button @click="saveProvider(p)">保存</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/http'

const providers = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await http.get('/model/providers')
    providers.value = res.data.map((p: any) => ({ ...p, baseUrl: p.default_base_url, apiKey: '', modelId: '' }))
  } catch {}
})

async function saveProvider(p: any) {
  try {
    await http.post('/model/config', { provider: p.id, base_url: p.baseUrl, api_key: p.apiKey, model_id: p.modelId })
    p.apiKey = ''
    alert('保存成功')
  } catch (e: any) {
    alert(e.response?.data?.detail || '保存失败')
  }
}
</script>

<style scoped>
.model-config h2 { margin-bottom: 1.5rem; }
.provider-card { background: #fff; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #e2e8f0; }
.provider-card h3 { margin-bottom: 1rem; }
.form-group { margin-bottom: .8rem; }
label { display: block; margin-bottom: .2rem; font-size: 14px; }
input { width: 100%; max-width: 400px; padding: .4rem; border: 1px solid #ddd; border-radius: 4px; }
button { padding: .4rem 1rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
</style>
