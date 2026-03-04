'use client'

import { useEffect, useState } from 'react'
import { format, differenceInDays } from 'date-fns'
import AxiosInstance from '@/api/AxiosInstance'
import Loading from '@/components/Loading'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function ManageSubscriptionPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [currentSub, setCurrentSub] = useState(null)
  const [plans, setPlans] = useState([])

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    try {
      const { data } = await AxiosInstance.get(
        '/api/billing/current-subscription/?plan_type=organization',
        { useTenant: true }
      )

      setCurrentSub(data.subscription || null)
      setPlans(data.plans || [])

    } catch (err) {
      toast.error("Failed to load subscription data")
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = async (planId) => {
    console.log("Upgrading to plan ID:", planId)
    try {
      await AxiosInstance.post(
        '/api/billing/upgrade-subscription/',
        { plan_id: planId },
        { useTenant: true }
      )
      toast.success("Plan change initiated!")
      fetchAllData()
    } catch {
      toast.error("Upgrade failed")
    }
  }

  const handleCancel = async () => {
    try {
      await AxiosInstance.post(
        '/api/billing/cancel/',
        {},
        { useTenant: true }
      )
      toast.success("Cancel request sent")
      fetchAllData()
    } catch {
      toast.error("Cancel failed")
    }
  }

  const handleBillingPortal = () => {
    window.location.href = '/api/billing/create-customer-portal/'
  }

  if (loading) return <Loading />

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-semibold mb-8">
        Manage Subscription
      </h1>

      {/* ================= CURRENT PLAN SECTION ================= */}

      {!currentSub ? (
        <div className="p-8 border rounded-2xl bg-red-50 text-center">
          <h2 className="text-2xl text-red-600 font-semibold mb-4">
            No Active Subscription
          </h2>
          <button
            onClick={() => router.push('/billing/plans')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
          >
            Buy Plan
          </button>
        </div>
      ) : (
        <div className="mb-10 border-2 border-green-500 bg-green-50 rounded-2xl p-8 shadow-sm">

          <div className="flex justify-between flex-wrap gap-6">

            <div>
              <h2 className="text-2xl font-bold text-green-700">
                {currentSub.plan_name} Plan
              </h2>

              <span className="inline-block mt-2 px-3 py-1 text-sm bg-green-600 text-white rounded-full">
                Active Plan
              </span>

              {currentSub.start_date && currentSub.end_date && (
                <>
                  <p className="mt-4 text-gray-700">
                    Billing Period:
                  </p>

                  <p className="font-medium text-gray-800">
                    {format(new Date(currentSub.start_date), 'PPP')} —{" "}
                    {format(new Date(currentSub.end_date), 'PPP')}
                  </p>

                  <p className="mt-2 font-semibold text-green-700">
                    {differenceInDays(
                      new Date(currentSub.end_date),
                      new Date()
                    )} days remaining
                  </p>
                </>
              )}
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={handleBillingPortal}
                className="bg-white border border-gray-300 hover:bg-gray-100 px-5 py-2.5 rounded-xl font-medium"
              >
                Manage Billing
              </button>

              <button
                onClick={handleCancel}
                className="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-xl font-medium"
              >
                Cancel Plan
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ================= AVAILABLE PLANS ================= */}

      <div>
        <h2 className="text-2xl font-semibold mb-6">
          Available Plans
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {

            const isCurrent =
              currentSub && currentSub.plan_id === plan.id

            return (
              <div
                key={plan.id}
                className={`relative border rounded-2xl p-6 transition-all duration-300 ${
                  isCurrent
                    ? 'border-green-500 bg-green-50 scale-105 shadow-lg'
                    : 'bg-white hover:shadow-xl'
                }`}
              >

                {isCurrent && (
                  <div className="absolute top-4 right-4 text-xs bg-green-600 text-white px-3 py-1 rounded-full">
                    Current
                  </div>
                )}

                <h3 className="text-xl font-semibold">
                  {plan.name}
                </h3>

                <p className="mt-2 text-3xl font-bold text-gray-800">
                  ${plan.price}
                  <span className="text-sm font-medium text-gray-500">
                    /{plan.billing_cycle}
                  </span>
                </p>

                <div className="mt-6">

                  {isCurrent ? (
                    <button
                      disabled
                      className="w-full py-3 rounded-xl bg-green-600 text-white font-semibold cursor-not-allowed"
                    >
                      Active Plan
                    </button>
                  ) : (
                    <button
                      onClick={() => handleUpgrade(plan.id)}
                      className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition"
                    >
                      Upgrade / Switch
                    </button>
                  )}

                </div>

              </div>
            )
          })}
        </div>
      </div>

    </div>
  )
}