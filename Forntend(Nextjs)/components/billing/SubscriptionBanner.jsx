'use client'

import { useRouter } from 'next/navigation'
import { differenceInDays, format } from 'date-fns'

export default function SubscriptionBanner({
  trialEndsAt,
  isTrial,
  hasActiveSubscription,
  subscriptionCurrentPeriodEnd,
  planName,
}) {
  const router = useRouter()
  const today = new Date()

  if (isTrial === undefined && hasActiveSubscription === undefined) {
    return null
  }

  const trialEnd = trialEndsAt ? new Date(trialEndsAt) : null
  const trialDaysLeft = trialEnd
    ? differenceInDays(trialEnd, today)
    : 0

  const planEnd = subscriptionCurrentPeriodEnd
    ? new Date(subscriptionCurrentPeriodEnd)
    : null

  const planDaysLeft = planEnd
    ? differenceInDays(planEnd, today)
    : 0

  // 🟢 Active Paid Plan
  if (hasActiveSubscription && planDaysLeft >= 0) {
    return (
      <div className="mb-6 rounded-xl border border-green-300 bg-green-50 p-5 flex justify-between items-center">
        <div>
          <h3 className="text-green-800 font-semibold text-lg">
            {planName} Plan Active
          </h3>
          <p className="text-green-700 text-sm mt-1">
            Valid until {format(planEnd, 'PPP')} • {planDaysLeft} days remaining
          </p>
        </div>

        <button
          onClick={() => router.push('/store/billing/manage_plan')}
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-2.5 rounded-lg font-medium"
        >
          Manage Plan
        </button>
      </div>
    )
  }

  // 🔴 Trial Expired
  if (!isTrial || trialDaysLeft < 0) {
    return (
      <div className="mb-6 rounded-xl border border-red-300 bg-red-50 p-5 flex justify-between items-center">
        <div>
          <h3 className="text-red-700 font-semibold text-lg">
            Free Trial Expired
          </h3>
          <p className="text-red-600 text-sm mt-1">
            Purchase a plan to continue using your store.
          </p>
        </div>

        <button
          onClick={() => router.push('/billing/plans')}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2.5 rounded-lg font-medium"
        >
          Buy Plan
        </button>
      </div>
    )
  }

  // 🟡 Trial Active
  return (
    <div className="mb-6 rounded-xl border border-yellow-300 bg-yellow-50 p-5 flex justify-between items-center">
      <div>
        <h3 className="text-yellow-800 font-semibold text-lg">
          Free Trial Active
        </h3>
        <p className="text-yellow-700 text-sm mt-1">
          Ends on {format(trialEnd, 'PPP')} • {trialDaysLeft} days remaining
        </p>
      </div>

      <button
        onClick={() => router.push('/billing/plans/org_subscription')}
        className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-2.5 rounded-lg font-medium"
      >
        Upgrade Plan
      </button>
    </div>
  )
}