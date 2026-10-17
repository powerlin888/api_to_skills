import http from './http'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  nickname: string
  role: string
  points: number
  created_at: string
}

export const authApi = {
  async register(email: string, nickname: string, password: string): Promise<TokenResponse> {
    const res = await http.post('/auth/register', { email, nickname, password })
    return res.data
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const res = await http.post('/auth/login', { email, password })
    return res.data
  },

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const res = await http.post('/auth/refresh', refreshToken)
    return res.data
  },

  async getMe(): Promise<UserResponse> {
    const res = await http.get('/auth/me')
    return res.data
  },
}
