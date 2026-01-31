import apiClient from './client'
import type { SessionLog, SessionCreate } from '../types'

export const sessionsApi = {
  list: async (params?: { date?: string; trainer?: string }) => {
    const response = await apiClient.get<SessionLog[]>('/sessions', { params })
    return response.data
  },

  getDaily: async (date: string) => {
    const response = await apiClient.get<SessionLog[]>(`/sessions/daily/${date}`)
    return response.data
  },

  getTrainers: async () => {
    const response = await apiClient.get<{ trainers: string[] }>('/sessions/trainers')
    return response.data
  },

  create: async (data: SessionCreate) => {
    const response = await apiClient.post<SessionLog>('/sessions', data)
    return response.data
  },

  update: async (id: number, data: Partial<SessionCreate>) => {
    const response = await apiClient.put<SessionLog>(`/sessions/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/sessions/${id}`)
    return response.data
  },

  getTodayStats: async () => {
    const response = await apiClient.get('/sessions/stats/today')
    return response.data
  },
}
