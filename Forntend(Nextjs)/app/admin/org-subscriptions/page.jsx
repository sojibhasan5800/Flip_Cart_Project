// app/admin/org-subscriptions/page.jsx
'use client'

import { useState, useEffect } from 'react'
import axios from '@/api/AxiosInstance'
import { Pencil, XCircle } from 'lucide-react'

const OrgSubscriptionsPage = () => {
  const [subscriptions, setSubscriptions] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchSubscriptions = async () => {
    try {
      const res = await axios.get('api/billing/org-subscriptions/')
      setSubscriptions(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubscriptions()
  }, [])

  const handleStatusChange = async (id, status) => {
    if (!confirm(`Are you sure to set status as ${status}?`)) return
    try {
      const res = await axios.patch(`api/billing/org-subscriptions/${id}/`, { status })
      setSubscriptions(subscriptions.map(sub => sub.id === id ? res.data : sub))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Organization Subscriptions</h1>
      {loading ? (
        <p>Loading...</p>
      ) : subscriptions.length === 0 ? (
        <p>No subscriptions found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full table-auto border border-slate-200 rounded">
            <thead className="bg-slate-100">
              <tr>
                <th className="p-2 border">Organization</th>
                <th className="p-2 border">Plan</th>
                <th className="p-2 border">Start Date</th>
                <th className="p-2 border">End Date</th>
                <th className="p-2 border">Status</th>
                <th className="p-2 border">Current Usage</th>
                <th className="p-2 border">Boosted Count</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {subscriptions.map(sub => (
                <tr key={sub.id} className="hover:bg-slate-50">
                  <td className="p-2 border">{sub.organization.business_name}</td>
                  <td className="p-2 border">{sub.plan.name} ({sub.plan.level})</td>
                  <td className="p-2 border">{new Date(sub.start_date).toLocaleDateString()}</td>
                  <td className="p-2 border">{sub.end_date ? new Date(sub.end_date).toLocaleDateString() : '-'}</td>
                  <td className="p-2 border capitalize">{sub.status}</td>
                  <td className="p-2 border">
                    Products: {sub.current_usage.products || 0} <br />
                    Boosted: {sub.current_usage.boosted || 0}
                  </td>
                  <td className="p-2 border">{sub.boosted_products_count}</td>
                  <td className="p-2 border flex gap-2">
                    <button
                      onClick={() => handleStatusChange(sub.id, 'active')}
                      className="text-green-500 hover:text-green-700"
                    >Activate</button>
                    <button
                      onClick={() => handleStatusChange(sub.id, 'cancelled')}
                      className="text-red-500 hover:text-red-700"
                    >Cancel</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default OrgSubscriptionsPage