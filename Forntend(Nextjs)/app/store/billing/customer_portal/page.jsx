'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AxiosInstance from '@/api/AxiosInstance'
import toast from 'react-hot-toast'

export default function ManageBillingPage() {

  const router = useRouter()
  const [loading, setLoading] = useState(false)

  const handleManageBilling = async () => {
    setLoading(true)
    try {
      const { data } = await AxiosInstance.post(
        '/api/billing/create-customer-portal/',
        {},
        { useTenant: true }
      )

      window.location.href = data.url  // ✅ real redirect

    } catch (error) {
      toast.error("Failed to open billing portal")
    }
    setLoading(false)
  }

  return (
    <div className="max-w-3xl mx-auto p-8">

      <h1 className="text-2xl font-semibold mb-6">
        Manage Billing
      </h1>

      <div className="border rounded-xl p-6 bg-white shadow-sm">

        <h2 className="text-lg font-medium mb-2">
          Billing & Payment Settings
        </h2>

        <p className="text-gray-600 text-sm mb-6">
          Manage your payment method, download invoices,
          update billing details, or cancel your subscription.
        </p>

        <button
          onClick={handleManageBilling}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium"
        >
          {loading ? "Redirecting..." : "Open Billing Portal"}
        </button>

        <button
          onClick={() => router.back()}
          className="ml-4 bg-gray-200 hover:bg-gray-300 text-gray-800 px-6 py-2.5 rounded-lg font-medium"
        >
          Go Back
        </button>

      </div>

    </div>
  )
}