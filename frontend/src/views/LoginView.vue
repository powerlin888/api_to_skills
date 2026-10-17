<template>
  <div class="login-container">
    <div class="login-card">
      <h2>{{ isRegister ? '注册' : '登录' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" required placeholder="请输入邮箱" />
        </div>
        <div v-if="isRegister" class="form-group">
          <label>昵称</label>
          <input v-model="nickname" required placeholder="请输入昵称" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" required minlength="8" placeholder="至少8个字符" />
        </div>
        <button type="submit" :disabled="loading">{{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}</button>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
      <p class="switch" @click="isRegister = !isRegister">
        {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const isRegister = ref(false)
const email = ref('')
const nickname = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register(email.value, nickname.value, password.value)
    }
    await auth.login(email.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    error.value = e.response?.data?.detail || '操作失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.login-card { background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.1); width: 360px; }
h2 { text-align: center; margin-bottom: 1.5rem; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: .3rem; font-size: 14px; }
input { width: 100%; padding: .5rem; border: 1px solid #ddd; border-radius: 4px; }
button { width: 100%; padding: .6rem; background: #4f46e5; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { opacity: .6; }
.error { color: #ef4444; font-size: 14px; margin-top: .5rem; }
.switch { text-align: center; margin-top: 1rem; color: #4f46e5; cursor: pointer; font-size: 14px; }
</style>
