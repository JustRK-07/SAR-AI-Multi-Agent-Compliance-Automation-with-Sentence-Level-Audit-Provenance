import { format, formatDistanceToNow } from 'date-fns'

export function formatCurrency(amount: number): string {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`
  } else {
    return `₹${amount.toLocaleString('en-IN')}`
  }
}

export function formatDate(dateString: string): string {
  return format(new Date(dateString), 'MMM dd, yyyy')
}

export function formatDateTime(dateString: string): string {
  return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
}

export function formatRelativeTime(dateString: string): string {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true })
}

export function formatAccountNumber(accountNumber: string): string {
  if (accountNumber.length > 4) {
    return `****${accountNumber.slice(-4)}`
  }
  return accountNumber
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function getRiskColor(score: number): string {
  if (score >= 80) return 'text-red-600 bg-red-50'
  if (score >= 60) return 'text-orange-600 bg-orange-50'
  if (score >= 40) return 'text-yellow-600 bg-yellow-50'
  return 'text-green-600 bg-green-50'
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-gray-600 bg-gray-100',
    in_review: 'text-blue-600 bg-blue-100',
    processing: 'text-blue-600 bg-blue-100',
    draft: 'text-yellow-600 bg-yellow-100',
    sar_generated: 'text-purple-600 bg-purple-100',
    reviewing: 'text-orange-600 bg-orange-100',
    approved: 'text-green-600 bg-green-100',
    submitted: 'text-green-700 bg-green-200',
    dismissed: 'text-gray-500 bg-gray-100',
    rejected: 'text-red-600 bg-red-100',
  }
  return colors[status] || 'text-gray-600 bg-gray-100'
}
