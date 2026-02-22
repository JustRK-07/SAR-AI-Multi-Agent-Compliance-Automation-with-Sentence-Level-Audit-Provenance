import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { alertService } from '@/services/alertService'
import { formatCurrency, formatDate, getRiskColor, getStatusColor } from '@/utils/formatters'
import type { AlertStatus } from '@/types'

export default function Alerts() {
  const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('')
  const [scenarioFilter, setScenarioFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['alerts', statusFilter, scenarioFilter, page],
    queryFn: () =>
      alertService.getAlerts({
        status: statusFilter || undefined,
        scenario: scenarioFilter || undefined,
        page,
        page_size: 10,
      }),
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Alert Queue</h1>
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search alerts..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as AlertStatus | '')}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in_review">In Review</option>
            <option value="sar_generated">SAR Generated</option>
            <option value="approved">Approved</option>
            <option value="submitted">Submitted</option>
          </select>

          {/* Scenario Filter */}
          <select
            value={scenarioFilter}
            onChange={(e) => setScenarioFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Scenarios</option>
            <option value="Structuring">Structuring</option>
            <option value="Layering">Layering</option>
            <option value="Rapid Movement">Rapid Movement</option>
            <option value="Collection Account">Collection Account</option>
          </select>
        </div>
      </div>

      <Card>
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading alerts...</div>
        ) : data?.alerts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No alerts found</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                    <th className="pb-3 px-2 font-medium">Alert ID</th>
                    <th className="pb-3 px-2 font-medium">Customer</th>
                    <th className="pb-3 px-2 font-medium">Scenario</th>
                    <th className="pb-3 px-2 font-medium">Risk</th>
                    <th className="pb-3 px-2 font-medium">Transactions</th>
                    <th className="pb-3 px-2 font-medium">Amount</th>
                    <th className="pb-3 px-2 font-medium">Status</th>
                    <th className="pb-3 px-2 font-medium">Date</th>
                    <th className="pb-3 px-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.alerts.map((alert) => (
                    <tr key={alert.id} className="hover:bg-gray-50">
                      <td className="py-4 px-2">
                        <span className="font-mono text-sm text-gray-900">{alert.id}</span>
                      </td>
                      <td className="py-4 px-2">
                        <div>
                          <p className="font-medium text-gray-900">{alert.customer_name}</p>
                          <p className="text-xs text-gray-500">{alert.account_number}</p>
                        </div>
                      </td>
                      <td className="py-4 px-2">
                        <span className="inline-flex px-2 py-1 bg-gray-100 rounded text-xs font-medium">
                          {alert.scenario}
                        </span>
                      </td>
                      <td className="py-4 px-2">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-bold ${getRiskColor(alert.risk_score)}`}
                        >
                          {alert.risk_score}
                        </span>
                      </td>
                      <td className="py-4 px-2">
                        <span className="text-sm">{alert.transaction_count}</span>
                      </td>
                      <td className="py-4 px-2">
                        <span className="text-sm font-medium">{formatCurrency(alert.total_amount)}</span>
                      </td>
                      <td className="py-4 px-2">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}
                        >
                          {alert.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-4 px-2">
                        <span className="text-sm text-gray-500">{formatDate(alert.created_at)}</span>
                      </td>
                      <td className="py-4 px-2">
                        <Link to={`/sar/${alert.id}`}>
                          <Button size="sm" variant="outline">
                            Review
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200 mt-4">
              <p className="text-sm text-gray-500">
                Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, data?.total || 0)} of {data?.total || 0} alerts
              </p>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setPage(p => p + 1)}
                  disabled={!data || page * 10 >= data.total}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
