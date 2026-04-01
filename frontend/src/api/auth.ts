import client from './client'

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  email: string
  name: string
}

export interface UserResponse {
  id: string
  email: string
  name: string
  is_active: boolean
  created_at: string
}

export const authApi = {
  login: (email: string, password: string) =>
    client.post<TokenResponse>('/auth/login', { email, password }),

  me: () => client.get<UserResponse>('/auth/me'),
}
