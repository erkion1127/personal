import apiClient from './client'
import type { Member, MemberSearchResult } from '../types'

export const membersApi = {
  list: async (params?: { limit?: number; offset?: number }) => {
    const response = await apiClient.get<Member[]>('/members', { params })
    return response.data
  },

  search: async (query: string) => {
    const response = await apiClient.get<{
      query: string
      count: number
      members: MemberSearchResult[]
    }>('/members/search', { params: { q: query } })
    return response.data
  },

  sync: async () => {
    const response = await apiClient.post<{
      success: boolean
      message: string
      count: number
      synced_at: string
    }>('/members/sync')
    return response.data
  },

  getStats: async () => {
    const response = await apiClient.get<{
      total: number
      synced_at: string | null
    }>('/members/stats')
    return response.data
  },
}
