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

  changePassword: (old_password: string, new_password: string) =>
    client.post<void>('/auth/change-password', { old_password, new_password }),

  createUser: (email: string, name: string, password: string) =>
    client.post<UserResponse>('/auth/users', { email, name, password }),

  listUsers: () =>
    client.get<UserResponse[]>('/auth/users'),
}
