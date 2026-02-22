import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Download, CheckCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/common/Button'
import NarrativePanel from '@/components/sar/NarrativePanel'
import AuditTrailPanel from '@/components/sar/AuditTrailPanel'
import TransactionGraph from '@/components/transactions/TransactionGraph'
import { alertService } from '@/services/alertService'
import { sarService } from '@/services/sarService'
import { auditService } from '@/services/auditService'
import { formatCurrency, getRiskColor, formatPercentage } from '@/utils/formatters'

export default function SARWorkspace() {
  const { alertId } = useParams<{ alertId: string }>()
  const queryClient = useQueryClient()
  const [selectedSentence, setSelectedSentence] = useState<number | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [currentAgent, setCurrentAgent] = useState<string | null>(null)

  // Fetch alert
  const { data: alert } = useQuery({
    queryKey: ['alert', alertId],
    queryFn: () => alertService.getAlert(alertId!),
    enabled: !!alertId,
  })

  // Fetch SAR (if exists)
  const { data: sar, refetch: refetchSAR } = useQuery({
    queryKey: ['sar', alertId],
    queryFn: () => sarService.getSARByAlert(alertId!),
    enabled: !!alertId,
    retry: false,
  })

  // Fetch evidence for selected sentence
  const { data: evidence, isLoading: evidenceLoading } = useQuery({
    queryKey: ['evidence', sar?.id, selectedSentence],
    queryFn: () => auditService.getSentenceEvidence(sar!.id, selectedSentence!),
    enabled: !!sar?.id && selectedSentence !== null,
  })

  // Generate SAR mutation
  const generateMutation = useMutation({
    mutationFn: () => sarService.generate(alertId!),
    onSuccess: async (data) => {
      // Poll for completion
      setIsGenerating(true)
      const pollInterval = setInterval(async () => {
        try {
          const status = await sarService.getTaskStatus(data.task_id)
          setGenerationProgress(status.progress)
          setCurrentAgent(status.current_agent || null)

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            setIsGenerating(false)
            refetchSAR()
            queryClient.invalidateQueries({ queryKey: ['alerts'] })
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            setIsGenerating(false)
            console.error('SAR generation failed:', status.error)
          }
        } catch (e) {
          clearInterval(pollInterval)
          setIsGenerating(false)
        }
      }, 1000)
    },
  })

  // Submit SAR mutation
  const submitMutation = useMutation({
    mutationFn: () => sarService.submit(sar!.id),
    onSuccess: () => {
      refetchSAR()
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  // Export PDF
  const handleExport = async () => {
    if (!sar) return
    const blob = await sarService.exportPDF(sar.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${sar.id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const agentNames: Record<string, string> = {
    data_analyst: 'Data Analyst',
    compliance: 'Compliance Specialist',
    writer: 'Narrative Writer',
    fact_checker: 'Fact Checker',
    editor: 'Editor',
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-10 w-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <FileText className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">SAR Workspace</h1>
              <p className="text-sm text-gray-500">Alert: {alertId}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {!sar ? (
              <Button
                onClick={() => generateMutation.mutate()}
                loading={isGenerating || generateMutation.isPending}
              >
                Generate SAR
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export PDF
                </Button>
                {sar.status !== 'submitted' && (
                  <Button
                    variant="success"
                    onClick={() => submitMutation.mutate()}
                    loading={submitMutation.isPending}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve & Submit
                  </Button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Alert Info Bar */}
        {alert && (
          <div className="mt-4 flex items-center space-x-6 text-sm">
            <div>
              <span className="text-gray-500">Customer:</span>{' '}
              <span className="font-medium">{alert.customer_name}</span>
            </div>
            <div>
              <span className="text-gray-500">Scenario:</span>{' '}
              <span className="inline-flex px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">
                {alert.scenario}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Risk:</span>{' '}
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold ${getRiskColor(alert.risk_score)}`}>
                {alert.risk_score}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Amount:</span>{' '}
              <span className="font-medium">{formatCurrency(alert.total_amount)}</span>
            </div>
            <div>
              <span className="text-gray-500">Transactions:</span>{' '}
              <span className="font-medium">{alert.transaction_count}</span>
            </div>
          </div>
        )}

        {/* Generation Progress */}
        {isGenerating && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Loader2 className="h-4 w-4 text-blue-600 animate-spin mr-2" />
                <span className="text-sm text-blue-700">
                  Generating SAR... {currentAgent && `(${agentNames[currentAgent] || currentAgent})`}
                </span>
              </div>
              <span className="text-sm font-medium text-blue-700">{generationProgress}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${generationProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Narrative Panel */}
        <div className="w-1/2 border-r border-gray-200 overflow-y-auto p-6 bg-white">
          {sar ? (
            <>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">SAR Narrative</h2>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">Confidence:</span>
                  <span className={`text-sm font-medium ${sar.confidence_score >= 0.95 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {formatPercentage(sar.confidence_score)}
                  </span>
                </div>
              </div>
              <NarrativePanel
                sentences={sar.sentences}
                selectedSentence={selectedSentence}
                onSentenceClick={setSelectedSentence}
              />
            </>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Click "Generate SAR" to create narrative</p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Audit Trail Panel */}
        <div className="w-1/2 overflow-y-auto p-6 bg-gray-50">
          <h2 className="text-lg font-semibold mb-4">Evidence Trail</h2>
          <AuditTrailPanel
            evidence={evidence}
            isLoading={evidenceLoading}
            selectedSentence={selectedSentence}
          />
        </div>
      </div>

      {/* Bottom: Transaction Graph */}
      {alertId && (
        <div className="h-64 border-t border-gray-200 bg-white">
          <TransactionGraph alertId={alertId} />
        </div>
      )}
    </div>
  )
}
