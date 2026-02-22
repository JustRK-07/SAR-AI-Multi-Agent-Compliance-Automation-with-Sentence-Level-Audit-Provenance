import api from './api'
import type { Alert, AlertListResponse, AlertStatus } from '@/types'

export const alertService = {
  // Get all alerts with optional filters
  getAlerts: async (params?: {
    status?: AlertStatus
    scenario?: string
    min_risk?: number
    page?: number
    page_size?: number
  }): Promise<AlertListResponse> => {
    const response = await api.get<AlertListResponse>('/alerts', { params })
    return response.data
  },

  // Get single alert by ID
  getAlert: async (alertId: string): Promise<Alert> => {
    const response = await api.get<Alert>(`/alerts/${alertId}`)
    return response.data
  },

  // Update alert status
  updateStatus: async (alertId: string, status: AlertStatus): Promise<void> => {
    await api.patch(`/alerts/${alertId}/status`, null, { params: { status } })
  },
}
