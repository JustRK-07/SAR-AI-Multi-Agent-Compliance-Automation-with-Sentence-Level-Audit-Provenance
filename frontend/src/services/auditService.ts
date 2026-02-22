import api from './api'
import type { AuditEvidence, AuditTrailResponse } from '@/types'

export const auditService = {
  // Get evidence for a specific sentence
  getSentenceEvidence: async (sarId: string, sentenceIndex: number): Promise<AuditEvidence> => {
    const response = await api.get<AuditEvidence>(`/audit/sar/${sarId}/evidence/${sentenceIndex}`)
    return response.data
  },

  // Get full audit trail for a SAR
  getFullAuditTrail: async (sarId: string): Promise<AuditTrailResponse> => {
    const response = await api.get<AuditTrailResponse>(`/audit/sar/${sarId}`)
    return response.data
  },
}
