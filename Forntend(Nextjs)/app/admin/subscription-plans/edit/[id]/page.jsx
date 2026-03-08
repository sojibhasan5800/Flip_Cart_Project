// app/admin/subscription-plans/edit/[id]/page.jsx
'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import axios from '@/api/AxiosInstance'
import { Switch } from '@headlessui/react'

const EditSubscriptionPlan = () => {
  const { id } = useParams()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    name: '',
    slug: '',
    level: 'basic',
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
  const [featuresInput, setFeaturesInput] = useState('{}')
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const res = await axios.get(`/api/billing/plans/${id}/`)
        setForm(res.data)
        setFeaturesInput(JSON.stringify(res.data.features, null, 2))
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchPlan()
  }, [id])

  const handleChange = e => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleFeaturesChange = e => {
    setFeaturesInput(e.target.value)
    try {
      const parsed = JSON.parse(e.target.value)
      setForm(prev => ({ ...prev, features: parsed }))
      setError('')
    } catch {
      setError('Invalid JSON')
    }
  }

  const handleSubmit = async e => {
    e.preventDefault()
    if (error) return
    try {
      await axios.put(`/api/billing/plans/${id}/`, form)
      router.push('/admin/subscription-plans')
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) return <p>Loading...</p>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Edit Subscription Plan</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block mb-1">Name</label>
            <input type="text" name="name" value={form.name} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label className="block mb-1">Slug</label>
            <input type="text" name="slug" value={form.slug} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>

          <div>
            <label>Level</label>
            <select name="plan_level" value={form.plan_level} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="basic">Basic</option>
              <option value="standard">Standard</option>
              <option value="premium">Premium</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div>
            <label>Type</label>
            <select name="plan_type" value={form.plan_type} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="general">General</option>
              <option value="boosting">Boosting</option>
              <option value="custom">Custom</option>
              <option value="organization">Organization</option>
            </select>
          </div>

          <div>
            <label>Price</label>
            <input type="number" name="price" value={form.price} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label>Currency</label>
            <input type="text" name="currency" value={form.currency} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>

          <div>
            <label>Billing Cycle</label>
            <select name="billing_cycle" value={form.billing_cycle} onChange={handleChange} className="w-full border p-2 rounded">
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div>
            <label>Duration Days</label>
            <input type="number" name="duration_days" value={form.duration_days} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>

          <div>
            <label>Max Users</label>
            <input type="number" name="max_users" value={form.max_users} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label>Max Products</label>
            <input type="number" name="max_products" value={form.max_products} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>

          <div>
            <label>Max Boosted Products</label>
            <input type="number" name="max_boosted_products" value={form.max_boosted_products} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
          <div>
            <label>Storage GB</label>
            <input type="number" name="storage_gb" value={form.storage_gb} onChange={handleChange} className="w-full border p-2 rounded" />
          </div>
        </div>

        {/* Features JSON Editor */}
        <div>
          <label className="block mb-1">Features (JSON)</label>
          <textarea
            value={featuresInput}
            onChange={handleFeaturesChange}
            rows={6}
            className="w-full border p-2 rounded font-mono text-sm"
          />
          {error && <p className="text-red-500">{error}</p>}
        </div>

        {/* Activate / Deactivate Toggle */}
        <div className="flex items-center gap-4">
          <Switch
            checked={form.is_active}
            onChange={val => setForm(prev => ({ ...prev, is_active: val }))}
            className={`${form.is_active ? 'bg-green-500' : 'bg-gray-300'} relative inline-flex items-center h-6 rounded-full w-11 transition-colors`}
          >
            <span
              className={`${form.is_active ? 'translate-x-6' : 'translate-x-1'} inline-block w-4 h-4 transform bg-white rounded-full transition-transform`}
            />
          </Switch>
          <span>{form.is_active ? 'Active' : 'Inactive'}</span>
        </div>

        <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mt-4">Save Changes</button>
      </form>
    </div>
  )
}

export default EditSubscriptionPlan