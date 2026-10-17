import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userId = ref('')
  const nickname = ref('')
  const role = ref('')
  const points = ref(0)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res = await authApi.login(email, password)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    await fetchMe()
  }

  async function register(email: string, nick: string, password: string) {
    const res = await authApi.register(email, nick, password)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
  }

  async function fetchMe() {
    try {
      const me = await authApi.getMe()
      userId.value = me.id
      nickname.value = me.nickname
      role.value = me.role
      points.value = me.points
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userId.value = ''
    nickname.value = ''
    role.value = ''
    points.value = 0
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { token, refreshToken, userId, nickname, role, points, isAuthenticated, login, register, fetchMe, logout }
})
