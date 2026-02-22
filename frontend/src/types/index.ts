// Alert Types
export type AlertStatus = 'pending' | 'in_review' | 'sar_generated' | 'approved' | 'submitted' | 'dismissed'

export interface Alert {
  id: string
  trigger_date: string
  scenario: string
  risk_score: number
  customer_id: string
  customer_name: string
  account_number: string
  status: AlertStatus
  transaction_count: number
  total_amount: number
  assigned_to?: string
  created_at: string
}

export interface AlertListResponse {
  alerts: Alert[]
  total: number
  page: number
  page_size: number
}

// SAR Types
export type SARStatus = 'pending' | 'processing' | 'draft' | 'reviewing' | 'approved' | 'submitted' | 'rejected'

export interface SAR {
  id: string
  alert_id: string
  narrative: string
  typology: string
  fincen_code: string
  status: SARStatus
  confidence_score: number
  sentence_count: number
  sentences: string[]
  created_at: string
  updated_at: string
  customer_name: string
  account_number: string
  total_amount: number
  transaction_count: number
}

export interface SARGenerateResponse {
  task_id: string
  sar_id: string
  status: SARStatus
  message: string
}

// Transaction Types
export type TransactionType = 'CASH_DEPOSIT' | 'CASH_WITHDRAWAL' | 'WIRE_TRANSFER' | 'ACH_TRANSFER' | 'CHECK_DEPOSIT' | 'INTERNAL_TRANSFER'

export interface Transaction {
  id: string
  alert_id: string
  date: string
  amount: number
  type: TransactionType
  direction: 'INBOUND' | 'OUTBOUND'
  source_account: string
  destination_account: string
  source_location?: string
  destination_location?: string
  description?: string
  is_suspicious: boolean
}

export interface GraphNode {
  id: string
  label: string
  location?: string
  is_subject: boolean
  is_high_risk: boolean
  balance?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  amount: number
  date: string
  type: TransactionType
}

export interface TransactionGraphResponse {
  accounts: GraphNode[]
  transactions: GraphEdge[]
  patterns_detected: string[]
}

// Audit Types
export interface ClaimVerification {
  claim: string
  expected_value: unknown
  actual_value: unknown
  is_verified: boolean
  confidence: number
}

export interface AuditEvidence {
  sentence: string
  sentence_index: number
  data_source: string
  sql_query: string
  query_results: Record<string, unknown>[]
  confidence: number
  reasoning: string
  claims: ClaimVerification[]
  llm_prompt?: string
  llm_response?: string
  template_used?: string
  retrieved_documents?: string[]
}

export interface AuditTrailResponse {
  sar_id: string
  total_sentences: number
  verified_sentences: number
  overall_confidence: number
  entries: AuditEvidence[]
  generation_timestamp: string
  total_queries_executed: number
  total_tokens_used: number
}

// Task Types
export interface GenerationTask {
  task_id: string
  sar_id: string
  alert_id: string
  status: 'processing' | 'completed' | 'failed'
  progress: number
  current_agent?: string
  error?: string
}
