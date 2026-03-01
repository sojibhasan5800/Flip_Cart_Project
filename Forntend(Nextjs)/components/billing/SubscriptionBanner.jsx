'use client'

import { useRouter } from 'next/navigation'
import { differenceInDays } from 'date-fns'

export default function SubscriptionBanner({
  trialEndsAt,
  isTrial,
  hasActiveSubscription,
}) {
  const router = useRouter()

  if (hasActiveSubscription) return null

  const today = new Date()
  const trialEnd = trialEndsAt ? new Date(trialEndsAt) : null
  const daysLeft = trialEnd ? differenceInDays(trialEnd, today) : 0

  // 🔴 Trial expired
  if (!isTrial || daysLeft < 0) {
    return (
      <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="text-red-700 font-semibold text-lg">
            Free trial expired
          </h3>
          <p className="text-red-600 text-sm mt-1">
            Your store is currently limited. Please purchase a plan to continue.
          </p>
        </div>

        <button
          onClick={() => router.push('/billing/plans/org_subscription')}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2.5 rounded-lg font-medium"
        >
          Buy a Plan
        </button>
      </div>
    )
  }

  // 🟡 Trial active
  return (
    <div className="mb-6 rounded-xl border border-yellow-300 bg-yellow-50 p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h3 className="text-yellow-800 font-semibold">
          Free trial active
        </h3>
        <p className="text-yellow-700 text-sm mt-1">
          {daysLeft} day{daysLeft !== 1 && 's'} remaining in your free trial
        </p>
      </div>

      <button
        onClick={() => router.push('/dashboard/billing/subscription')}
        className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-2.5 rounded-lg font-medium"
      >
        Upgrade Plan
      </button>
    </div>
  )
}