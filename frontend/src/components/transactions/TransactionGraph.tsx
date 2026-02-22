import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { transactionService } from '@/services/transactionService'
import { formatCurrency } from '@/utils/formatters'

interface TransactionGraphProps {
  alertId: string
}

export default function TransactionGraph({ alertId }: TransactionGraphProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['transactionGraph', alertId],
    queryFn: () => transactionService.getTransactionGraph(alertId),
    enabled: !!alertId,
  })

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [], edges: [] }

    // Position nodes in a layout
    const accountNodes: Node[] = data.accounts.map((account, i) => {
      // Simple grid layout
      const col = i % 5
      const row = Math.floor(i / 5)

      return {
        id: account.id,
        position: { x: col * 200 + 50, y: row * 120 + 50 },
        data: {
          label: (
            <div className="text-center">
              <div className="font-bold text-xs">
                {account.is_subject ? '★ ' : ''}
                ****{account.id.slice(-4)}
              </div>
              {account.location && (
                <div className="text-[10px] text-gray-500">{account.location}</div>
              )}
            </div>
          ),
        },
        style: {
          background: account.is_subject
            ? '#dbeafe'
            : account.is_high_risk
            ? '#fee2e2'
            : '#f3f4f6',
          border: account.is_subject
            ? '2px solid #3b82f6'
            : account.is_high_risk
            ? '2px solid #ef4444'
            : '1px solid #d1d5db',
          borderRadius: '8px',
          padding: '8px 12px',
          fontSize: '12px',
        },
      }
    })

    const transactionEdges: Edge[] = data.transactions.map((txn) => ({
      id: txn.id,
      source: txn.source,
      target: txn.target,
      label: formatCurrency(txn.amount),
      labelStyle: { fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: '#fff', fillOpacity: 0.8 },
      animated: true,
      style: {
        stroke: txn.amount > 100000 ? '#ef4444' : '#6366f1',
        strokeWidth: Math.min(Math.max(txn.amount / 50000, 1), 4),
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: txn.amount > 100000 ? '#ef4444' : '#6366f1',
      },
    }))

    return { nodes: accountNodes, edges: transactionEdges }
  }, [data])

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <p className="text-gray-400">Loading transaction graph...</p>
      </div>
    )
  }

  if (!data || data.accounts.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <p className="text-gray-400">No transaction data available</p>
      </div>
    )
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#e5e7eb" gap={20} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.style?.border?.toString().includes('3b82f6')) return '#3b82f6'
            if (node.style?.border?.toString().includes('ef4444')) return '#ef4444'
            return '#9ca3af'
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>

      {/* Patterns Legend */}
      {data.patterns_detected.length > 0 && (
        <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg border border-gray-200 max-w-xs">
          <h4 className="text-xs font-semibold text-gray-700 mb-2">Patterns Detected</h4>
          <ul className="space-y-1">
            {data.patterns_detected.map((pattern, i) => (
              <li key={i} className="text-xs text-gray-600 flex items-start">
                <span className="text-red-500 mr-1">●</span>
                {pattern}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded mr-2"></div>
            <span>Subject Account</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-100 border-2 border-red-500 rounded mr-2"></div>
            <span>High-Risk Location</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-gray-100 border border-gray-300 rounded mr-2"></div>
            <span>Other Account</span>
          </div>
        </div>
      </div>
    </div>
  )
}
