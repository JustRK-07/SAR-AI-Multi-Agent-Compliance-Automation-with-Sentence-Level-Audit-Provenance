import { CheckCircle, AlertTriangle, Database, Code, Brain, FileText } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { cn } from '@/utils/cn'
import type { AuditEvidence } from '@/types'

interface AuditTrailPanelProps {
  evidence: AuditEvidence | undefined
  isLoading: boolean
  selectedSentence: number | null
}

export default function AuditTrailPanel({
  evidence,
  isLoading,
  selectedSentence,
}: AuditTrailPanelProps) {
  if (selectedSentence === null) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Click a sentence to view evidence</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-pulse text-gray-400">Loading evidence...</div>
      </div>
    )
  }

  if (!evidence) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>No evidence found for this sentence</p>
      </div>
    )
  }

  const confidenceColor = evidence.confidence >= 0.95
    ? 'text-green-600 bg-green-50 border-green-200'
    : evidence.confidence >= 0.7
    ? 'text-yellow-600 bg-yellow-50 border-yellow-200'
    : 'text-red-600 bg-red-50 border-red-200'

  return (
    <div className="space-y-4">
      {/* Selected Sentence */}
      <Card className="border-blue-200 bg-blue-50">
        <div className="flex items-start space-x-3">
          <div className="h-6 w-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-bold">{evidence.sentence_index + 1}</span>
          </div>
          <p className="text-sm text-gray-700">{evidence.sentence}</p>
        </div>
      </Card>

      {/* Confidence Score */}
      <Card className={cn('border', confidenceColor)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {evidence.confidence >= 0.95 ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
            )}
            <span className="font-medium">Confidence Score</span>
          </div>
          <span className="text-2xl font-bold">
            {(evidence.confidence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className={cn(
                'h-2.5 rounded-full transition-all',
                evidence.confidence >= 0.95 ? 'bg-green-500' :
                evidence.confidence >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
              )}
              style={{ width: `${evidence.confidence * 100}%` }}
            />
          </div>
        </div>
        {evidence.confidence < 0.95 && (
          <p className="mt-2 text-sm text-yellow-700">
            Low confidence - Review recommended
          </p>
        )}
      </Card>

      {/* Data Source */}
      <Card>
        <div className="flex items-center space-x-2 mb-2">
          <Database className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-500">Data Source</span>
        </div>
        <p className="font-mono text-sm bg-gray-100 p-2 rounded">
          {evidence.data_source}
        </p>
      </Card>

      {/* SQL Query */}
      {evidence.sql_query && evidence.sql_query !== 'N/A' && (
        <Card>
          <div className="flex items-center space-x-2 mb-2">
            <Code className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-500">SQL Query</span>
          </div>
          <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto">
            {evidence.sql_query}
          </pre>
        </Card>
      )}

      {/* Query Results */}
      {evidence.query_results && evidence.query_results.length > 0 && (
        <Card>
          <div className="flex items-center space-x-2 mb-2">
            <Database className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-500">Query Results</span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {Object.keys(evidence.query_results[0]).map((key) => (
                    <th
                      key={key}
                      className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                    >
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {evidence.query_results.slice(0, 5).map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((val, j) => (
                      <td key={j} className="px-3 py-2 whitespace-nowrap">
                        {String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {evidence.query_results.length > 5 && (
              <p className="text-xs text-gray-500 mt-2">
                Showing 5 of {evidence.query_results.length} results
              </p>
            )}
          </div>
        </Card>
      )}

      {/* Claim Verifications */}
      {evidence.claims && evidence.claims.length > 0 && (
        <Card>
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-500">Claim Verifications</span>
          </div>
          <div className="space-y-2">
            {evidence.claims.map((claim, i) => (
              <div
                key={i}
                className={cn(
                  'p-2 rounded text-sm flex items-center justify-between',
                  claim.is_verified ? 'bg-green-50' : 'bg-red-50'
                )}
              >
                <span>{claim.claim}</span>
                {claim.is_verified ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Reasoning */}
      {evidence.reasoning && (
        <Card>
          <div className="flex items-center space-x-2 mb-2">
            <Brain className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-500">Reasoning</span>
          </div>
          <p className="text-sm text-gray-700">{evidence.reasoning}</p>
        </Card>
      )}
    </div>
  )
}
