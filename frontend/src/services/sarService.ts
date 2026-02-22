import api from './api'
import type { SAR, SARGenerateResponse, SARStatus, GenerationTask } from '@/types'

export const sarService = {
  // Generate SAR for an alert
  generate: async (alertId: string): Promise<SARGenerateResponse> => {
    const response = await api.post<SARGenerateResponse>('/sar/generate', { alert_id: alertId })
    return response.data
  },

  // Get generation task status
  getTaskStatus: async (taskId: string): Promise<GenerationTask> => {
    const response = await api.get<GenerationTask>(`/sar/task/${taskId}`)
    return response.data
  },

  // Get SAR by ID
  getSAR: async (sarId: string): Promise<SAR> => {
    const response = await api.get<SAR>(`/sar/${sarId}`)
    return response.data
  },

  // Get SAR by alert ID
  getSARByAlert: async (alertId: string): Promise<SAR> => {
    const response = await api.get<SAR>(`/sar/by-alert/${alertId}`)
    return response.data
  },

  // Update SAR narrative
  updateNarrative: async (sarId: string, narrative: string): Promise<void> => {
    await api.patch(`/sar/${sarId}`, { narrative })
  },

  // Update SAR status
  updateStatus: async (sarId: string, status: SARStatus): Promise<void> => {
    await api.patch(`/sar/${sarId}`, { status })
  },

  // Submit SAR for filing
  submit: async (sarId: string, approvedBy: string = 'analyst'): Promise<{ filing_id: string }> => {
    const response = await api.post(`/sar/${sarId}/submit`, null, {
      params: { approved_by: approvedBy },
    })
    return response.data
  },

  // Export SAR as PDF
  exportPDF: async (sarId: string): Promise<Blob> => {
    const response = await api.get(`/sar/${sarId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },
}
