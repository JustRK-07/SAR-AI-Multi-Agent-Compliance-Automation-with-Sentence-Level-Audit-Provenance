import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { AlertTriangle, FileText, CheckCircle, Clock, ArrowRight } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { alertService } from '@/services/alertService'
import { formatCurrency, formatRelativeTime, getRiskColor, getStatusColor } from '@/utils/formatters'

export default function Dashboard() {
  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['alerts', 'dashboard'],
    queryFn: () => alertService.getAlerts({ page_size: 5 }),
  })

  // Calculate stats
  const stats = {
    pending: alertsData?.alerts.filter(a => a.status === 'pending').length || 0,
    inReview: alertsData?.alerts.filter(a => a.status === 'in_review').length || 0,
    sarGenerated: alertsData?.alerts.filter(a => a.status === 'sar_generated').length || 0,
    submitted: alertsData?.alerts.filter(a => a.status === 'submitted').length || 0,
  }

  return (
    <div className="p-6 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-amber-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Pending Alerts</p>
              <p className="text-3xl font-bold text-amber-600">{stats.pending}</p>
            </div>
            <div className="h-12 w-12 bg-amber-100 rounded-full flex items-center justify-center">
              <Clock className="h-6 w-6 text-amber-600" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">In Review</p>
              <p className="text-3xl font-bold text-blue-600">{stats.inReview}</p>
            </div>
            <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">SAR Generated</p>
              <p className="text-3xl font-bold text-purple-600">{stats.sarGenerated}</p>
            </div>
            <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Submitted</p>
              <p className="text-3xl font-bold text-green-600">{stats.submitted}</p>
            </div>
            <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* High Priority Alerts */}
      <Card
        title="High Priority Alerts"
        action={
          <Link
            to="/alerts"
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center"
          >
            View all <ArrowRight className="h-4 w-4 ml-1" />
          </Link>
        }
      >
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading alerts...</div>
        ) : alertsData?.alerts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No alerts found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase tracking-wider">
                  <th className="pb-3 font-medium">Alert ID</th>
                  <th className="pb-3 font-medium">Customer</th>
                  <th className="pb-3 font-medium">Scenario</th>
                  <th className="pb-3 font-medium">Risk Score</th>
                  <th className="pb-3 font-medium">Amount</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Created</th>
                  <th className="pb-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {alertsData?.alerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-gray-50">
                    <td className="py-3">
                      <span className="font-mono text-sm">{alert.id}</span>
                    </td>
                    <td className="py-3">
                      <div>
                        <p className="font-medium text-gray-900">{alert.customer_name}</p>
                        <p className="text-xs text-gray-500">{alert.account_number}</p>
                      </div>
                    </td>
                    <td className="py-3">
                      <span className="text-sm">{alert.scenario}</span>
                    </td>
                    <td className="py-3">
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(alert.risk_score)}`}>
                        {alert.risk_score}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="text-sm font-medium">{formatCurrency(alert.total_amount)}</span>
                    </td>
                    <td className="py-3">
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                        {alert.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="text-xs text-gray-500">{formatRelativeTime(alert.created_at)}</span>
                    </td>
                    <td className="py-3">
                      <Link
                        to={`/sar/${alert.id}`}
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        Review
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
