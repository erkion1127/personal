import apiClient from './client'
import type { DashboardData } from '../types'

export const dashboardApi = {
  getToday: async () => {
    const response = await apiClient.get<DashboardData>('/dashboard/today')
    return response.data
  },
}
