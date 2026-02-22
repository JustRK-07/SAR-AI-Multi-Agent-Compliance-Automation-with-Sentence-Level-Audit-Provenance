import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card } from '@/components/common/Card'
import { alertService } from '@/services/alertService'
import { formatCurrency, formatDate, getStatusColor } from '@/utils/formatters'

export default function History() {
  const { data, isLoading } = useQuery({
    queryKey: ['alerts', 'history'],
    queryFn: () =>
      alertService.getAlerts({
        status: 'submitted',
        page_size: 50,
      }),
  })

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">SAR History</h1>

      <Card>
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading history...</div>
        ) : data?.alerts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No submitted SARs found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                  <th className="pb-3 px-2 font-medium">Alert ID</th>
                  <th className="pb-3 px-2 font-medium">Customer</th>
                  <th className="pb-3 px-2 font-medium">Scenario</th>
                  <th className="pb-3 px-2 font-medium">Amount</th>
                  <th className="pb-3 px-2 font-medium">Status</th>
                  <th className="pb-3 px-2 font-medium">Submitted</th>
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
                      <span className="text-sm font-medium">{formatCurrency(alert.total_amount)}</span>
                    </td>
                    <td className="py-4 px-2">
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="py-4 px-2">
                      <span className="text-sm text-gray-500">{formatDate(alert.created_at)}</span>
                    </td>
                    <td className="py-4 px-2">
                      <Link
                        to={`/sar/${alert.id}`}
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
