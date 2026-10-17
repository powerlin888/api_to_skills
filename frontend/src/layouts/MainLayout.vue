<template>
  <div class="layout">
    <aside class="sidebar">
      <h3 class="logo">Skills平台</h3>
      <nav>
        <router-link to="/">首页</router-link>
        <router-link to="/pdf-upload">PDF上传</router-link>
        <router-link to="/agent-config">智能体配置</router-link>
        <router-link to="/model-config">模型配置</router-link>
        <router-link to="/community">社区</router-link>
      </nav>
      <div class="user-info" v-if="auth.nickname">
        <span>{{ auth.nickname }}</span>
        <span class="points">{{ auth.points }}积分</span>
        <button @click="auth.logout(); $router.push('/login')">退出</button>
      </div>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
onMounted(() => { if (auth.isAuthenticated) auth.fetchMe() })
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.sidebar { width: 220px; background: #1e293b; color: #fff; padding: 1rem; display: flex; flex-direction: column; }
.logo { font-size: 18px; margin-bottom: 1.5rem; text-align: center; }
nav { display: flex; flex-direction: column; gap: .5rem; flex: 1; }
nav a { color: #94a3b8; text-decoration: none; padding: .5rem; border-radius: 4px; transition: all .2s; }
nav a:hover, nav a.router-link-active { color: #fff; background: #334155; }
.user-info { margin-top: auto; padding-top: 1rem; border-top: 1px solid #334155; display: flex; flex-direction: column; gap: .3rem; font-size: 13px; }
.points { color: #fbbf24; }
button { background: none; border: 1px solid #64748b; color: #94a3b8; padding: .3rem; border-radius: 4px; cursor: pointer; font-size: 12px; }
.content { flex: 1; padding: 2rem; background: #f8fafc; }
</style>
