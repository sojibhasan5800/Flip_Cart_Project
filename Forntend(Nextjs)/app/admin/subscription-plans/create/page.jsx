// app/admin/subscription-plans/create/page.jsx
'use client'

import { useState } from 'react'
import axios from '@/api/AxiosInstance'
import { useRouter } from 'next/navigation'

const SubscriptionPlanForm = () => {
  const router = useRouter()
  const [form, setForm] = useState({
    name: '',
    slug: '',
    plan_level: 'basic',
    plan_type: 'general',
    price: 0,
    currency: 'USD',
    billing_cycle: 'monthly',
    duration_days: 30,
    max_users: 1,
    max_products: 100,
    max_boosted_products: 0,
    storage_gb: 5,
    features: {},
    is_active: true,
  })

  const handleChange = e => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async e => {
    e.preventDefault()
    try {
      await axios.post('api/billing/plans/', form)
      router.push('/admin/subscription-plans')
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Create Subscription Plan</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
        <div>
          <label className="block mb-1">Name</label>
          <input type="text" name="name" value={form.name} onChange={handleChange} className="w-full border p-2 rounded" />
        </div>
        <div>
          <label className="block mb-1">Slug</label>
          <input type="text" name="slug" value={form.slug} onChange={handleChange} className="w-full border p-2 rounded" />
        </div>
        <div className="flex gap-2">
          <div className="flex-1">
            <label>Level</label>
            <select name="plan_level" value={form.plan_level} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="basic">Basic</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div className="flex-1">
            <label>Type</label>
            <select name="plan_type" value={form.plan_type} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="general">General</option>
              <option value="boosting">Boosting</option>
              <option value="custom">Custom</option>
              <option value="organization">Organization</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label>Price</label>
            <input type="number" name="price" value={form.price} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div className="flex-1">
            <label>Currency</label>
            <input type="text" name="currency" value={form.currency} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label>Billing Cycle</label>
            <select name="billing_cycle" value={form.billing_cycle} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div className="flex-1">
            <label>Duration Days</label>
            <input type="number" name="duration_days" value={form.duration_days} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
        </div>

        <button type="submit" className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">Create Plan</button>
      </form>
    </div>
  )
}

export default SubscriptionPlanForm