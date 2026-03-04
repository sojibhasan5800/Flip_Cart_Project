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
      console.log("Fetched subscription data:", data)

    } catch (err) {
      toast.error("Failed to load subscription data")
    } finally {
      setLoading(false)
    }
  }

const handlePlanChange = async (plan) => {
  if (!currentSub) return

  // Convert string prices to numbers
  const planPrice = parseFloat(plan.price)
  const currentPrice = parseFloat(currentSub.price)

  try {
    if (planPrice > currentPrice) {
      // Upgrade immediately
      await AxiosInstance.post(
        '/api/billing/upgrade-subscription/',
        { plan_id: plan.id },
        { useTenant: true }
      )
      console.log("Upgrade response:", response)
      toast.success("Upgrade initiated successfully!")
    } else if (planPrice < currentPrice) {
      // Downgrade at period end
      await AxiosInstance.post(
        '/api/billing/downgrade-at-period-end/',
        { plan_id: plan.id },
        { useTenant: true }
      )
      toast.success("Downgrade scheduled at period end!")
    } else {
      toast("You are already on this plan")
      return
    }

    fetchAllData()  // Refresh plans & current subscription

  } catch (err) {
    toast.error("Plan change failed")
    console.error(err)
  }
}

const handleCancel = async () => {
  if (!currentSub || currentSub.cancel_at_period_end) {
    toast("Subscription already scheduled for cancellation");
    return;
  }

  try {
    await AxiosInstance.post(
      '/api/billing/cancel-subscription/',
      {},
      { useTenant: true }
    )
    toast.success(`Subscription will cancel at period end (${currentSub.end_date})`)
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
                {currentSub.cancel_at_period_end && (
      <span className="inline-block mt-2 px-3 py-1 text-sm bg-orange-600 text-white rounded-full">
          Cancellation Scheduled
        </span>
      )}

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
                    onClick={() => handlePlanChange(plan)}
                    className={`w-full py-3 rounded-xl font-semibold transition ${
                      parseFloat(plan.price) > parseFloat(currentSub?.price || 0)
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-yellow-500 hover:bg-yellow-600 text-white'
                    }`}
                  >
                    {parseFloat(plan.price) > parseFloat(currentSub?.price || 0) ? 'Upgrade' : 'Downgrade'}
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