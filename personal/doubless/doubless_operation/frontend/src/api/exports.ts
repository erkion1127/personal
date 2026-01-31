import apiClient from './client'
import type { ExportLog, ExportRequest } from '../types'

export const exportsApi = {
  list: async (limit?: number) => {
    const response = await apiClient.get<{ exports: ExportLog[] }>('/exports', {
      params: { limit },
    })
    return response.data
  },

  getPending: async () => {
    const response = await apiClient.get<{
      pending_count: number
      message: string
    }>('/exports/pending')
    return response.data
  },

  create: async (data: ExportRequest) => {
    const response = await apiClient.post<ExportLog>('/exports', data)
    return response.data
  },

  download: (exportId: string) => {
    return `${apiClient.defaults.baseURL}/exports/${exportId}/download`
  },
}
