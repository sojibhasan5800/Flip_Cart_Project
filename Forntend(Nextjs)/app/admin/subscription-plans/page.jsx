// app/admin/subscription-plans/page.jsx
'use client'

import { useState, useEffect } from 'react'
import axios from '@/api/AxiosInstance'
import { Plus, Edit, Trash2 } from 'lucide-react'
import Link from 'next/link'

const SubscriptionPlansPage = () => {
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchPlans = async () => {
    try {
      const res = await axios.get('/admin/plans/')
      setPlans(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPlans()
  }, [])

  const handleDelete = async (id) => {
    if (!confirm('Are you sure to delete this plan?')) return
    try {
      await axios.delete(`/admin/plans/${id}/`)
      setPlans(plans.filter(plan => plan.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Subscription Plans</h1>
        <Link href="/admin/subscription-plans/create" className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
          <Plus size={18} /> Add Plan
        </Link>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : plans.length === 0 ? (
        <p>No subscription plans found.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full table-auto border border-slate-200 rounded">
            <thead className="bg-slate-100">
              <tr>
                <th className="p-2 border">Name</th>
                <th className="p-2 border">Level</th>
                <th className="p-2 border">Type</th>
                <th className="p-2 border">Price</th>
                <th className="p-2 border">Billing Cycle</th>
                <th className="p-2 border">Status</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {plans.map(plan => (
                <tr key={plan.id} className="hover:bg-slate-50">
                  <td className="p-2 border">{plan.name}</td>
                  <td className="p-2 border capitalize">{plan.level}</td>
                  <td className="p-2 border capitalize">{plan.plan_type}</td>
                  <td className="p-2 border">{plan.price} {plan.currency}</td>
                  <td className="p-2 border capitalize">{plan.billing_cycle}</td>
                  <td className="p-2 border">{plan.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="p-2 border flex gap-2">
                    <Link href={`/admin/subscription-plans/edit/${plan.id}`} className="text-blue-500 hover:text-blue-700"><Edit size={16} /></Link>
                    <button onClick={() => handleDelete(plan.id)} className="text-red-500 hover:text-red-700"><Trash2 size={16} /></button>
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

export default SubscriptionPlansPage