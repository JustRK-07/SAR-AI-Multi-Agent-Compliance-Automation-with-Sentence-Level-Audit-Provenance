import api from './api'
import type { Transaction, TransactionGraphResponse } from '@/types'

export const transactionService = {
  // Get transactions for an alert
  getTransactions: async (alertId: string, limit: number = 100): Promise<{
    transactions: Transaction[]
    total: number
    total_amount: number
  }> => {
    const response = await api.get('/transactions', {
      params: { alert_id: alertId, limit },
    })
    return response.data
  },

  // Get transaction graph data for visualization
  getTransactionGraph: async (alertId: string): Promise<TransactionGraphResponse> => {
    const response = await api.get<TransactionGraphResponse>(`/transactions/graph/${alertId}`)
    return response.data
  },
}
