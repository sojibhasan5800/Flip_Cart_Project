// app/admin/boosts/page.jsx
'use client'

import { useState, useEffect } from 'react'
import axios from '@/api/AxiosInstance'
import { XCircle } from 'lucide-react'

const BoostsPage = () => {
  const [boosts, setBoosts] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchBoosts = async () => {
    try {
      const res = await axios.get('/admin/boosts/')
      setBoosts(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBoosts()
  }, [])

  const handleDeactivate = async (id) => {
    if (!confirm('Are you sure you want to deactivate this boost?')) return
    try {
      const res = await axios.patch(`/admin/boosts/${id}/`, { is_active: false })
      setBoosts(boosts.map(b => b.id === id ? res.data : b))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Active Boosted Products</h1>
      {loading ? (
        <p>Loading...</p>
      ) : boosts.length === 0 ? (
        <p>No active boosts found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full table-auto border border-slate-200 rounded">
            <thead className="bg-slate-100">
              <tr>
                <th className="p-2 border">Organization</th>
                <th className="p-2 border">Product</th>
                <th className="p-2 border">Priority Level</th>
                <th className="p-2 border">Start Date</th>
                <th className="p-2 border">End Date</th>
                <th className="p-2 border">Status</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {boosts.map(boost => (
                <tr key={boost.id} className="hover:bg-slate-50">
                  <td className="p-2 border">{boost.organization_subscription.organization.business_name}</td>
                  <td className="p-2 border">{boost.product?.product_name || 'N/A'}</td>
                  <td className="p-2 border">
                    {boost.priority_level === 1 ? 'Standard' : boost.priority_level === 2 ? 'Premium' : 'VIP'}
                  </td>
                  <td className="p-2 border">{new Date(boost.boost_start_date).toLocaleDateString()}</td>
                  <td className="p-2 border">{boost.boost_end_date ? new Date(boost.boost_end_date).toLocaleDateString() : '-'}</td>
                  <td className="p-2 border">{boost.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="p-2 border flex gap-2">
                    {boost.is_active && (
                      <button
                        onClick={() => handleDeactivate(boost.id)}
                        className="text-red-500 hover:text-red-700 flex items-center gap-1"
                      >
                        <XCircle size={16} /> Deactivate
                      </button>
                    )}
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

export default BoostsPage