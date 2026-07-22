
// export default function PricingPage() {
//     return (
//         <div className='mx-auto max-w-[700px] my-28'>
//             {/* Pricing Table */}

//         </div>
//     )
// }

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import AxiosInstance from '@/api/AxiosInstance'
// import { loadStripe } from '@stripe/stripe-js'
// import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import Loading from '@/components/Loading'
import PaymentMethodModal from '@/components/billing/PaymentMethodModal'

// Stripe
// const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)

export default function PricingPage() {
    const [loading, setLoading] = useState(true)
    const [plans, setPlans] = useState([])
    const [selectedPlan, setSelectedPlan] = useState(null)
    const [showPaymentModal, setShowPaymentModal] = useState(false)
    const router = useRouter()

    useEffect(() => {
        fetchPlans()
    }, [])

    const fetchPlans = async () => {
        try {
            const res = await AxiosInstance.get('/api/billing/plus-membership/')
            setPlans(res.data)
            console.log('Plans fetched:', res.data)
        } catch (err) {
            toast.error('Failed to load plans')
        } finally {
            setLoading(false)
        }
    }

    const handlePurchaseClick = (plan) => {
        setSelectedPlan(plan)
        setShowPaymentModal(true)
    }

    const handlePaymentSuccess = async (planId) => {
        toast.success('Plan purchased successfully! You can now boost products.')
        // Redirect to manage products
        router.push('/store/manage-product')
    }

    if (loading) return <Loading />

    return (
        <div className='mx-auto max-w-[700px] my-28'>
            <h1 className="text-3xl font-bold text-center mb-12 text-gray-800">Choose Your Plus_Membership Plan</h1>

           <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
    {plans.map((plan) => (
        <div
            key={plan.id}
            className={`bg-white rounded-xl shadow-lg p-6 flex flex-col items-center transition duration-300 hover:scale-105 ${
                plan.plan_level === "enterprise"
                    ? "border-4 border-indigo-500"
                    : ""
            }`}
        >
            <h2 className="text-2xl font-semibold mb-3 text-gray-800">
                {plan.plan_name}
            </h2>

            <p className="text-4xl font-bold text-indigo-600">
                ${plan.price}
            </p>

            <p className="text-sm text-gray-500 mb-6 capitalize">
                {plan.billing_cycle}
            </p>

            <ul className="w-full mb-6 space-y-2 text-sm text-gray-700">

    <li>
        ✅ Duration :
        <strong> {plan.duration_days} Days</strong>
    </li>

    <li>
        💳 Billing :
        <strong> {plan.billing_cycle}</strong>
    </li>

    <li>
        🚚 Free Shipping :
        <strong>
            {plan.free_shipping ? " Yes" : " No"}
        </strong>
    </li>

    {plan.free_shipping && (
        <>
            <li>
                📦 Minimum Order :
                <strong> ${plan.free_shipping_min_order}</strong>
            </li>

            <li>
                🚛 Free Shipping Limit :
                <strong>
                    {" "}
                    {plan.max_free_shipping_orders === 999999
                        ? "Unlimited"
                        : plan.max_free_shipping_orders}
                </strong>
            </li>
        </>
    )}

    {plan.shipping_discount_percent > 0 && (
        <li>
            🎁 Shipping Discount :
            <strong>
                {" "}
                {plan.shipping_discount_percent}%
            </strong>
        </li>
    )}

    {plan.cashback_percent > 0 && (
        <li>
            💰 Cashback :
            <strong>
                {" "}
                {plan.cashback_percent}%
            </strong>
        </li>
    )}

    {Number(plan.reward_points_multiplier) > 1 && (
        <li>
            ⭐ Reward Points :
            <strong>
                {" "}
                x{plan.reward_points_multiplier}
            </strong>
        </li>
    )}

    {plan.priority_order_processing && (
        <li>⚡ Priority Order Processing</li>
    )}

    {plan.priority_customer_support && (
        <li>🎧 Priority Customer Support</li>
    )}

    {plan.early_access_sale && (
        <li>🛍 Early Sale Access</li>
    )}

    {plan.exclusive_deals && (
        <li>🔥 Exclusive Deals</li>
    )}

    {plan.monthly_order_limit > 0 && (
        <li>
            📦 Monthly Order Limit :
            <strong>
                {" "}
                {plan.monthly_order_limit}
            </strong>
        </li>
    )}

    {Number(plan.monthly_spending_limit) > 0 && (
        <li>
            💵 Monthly Spending :
            <strong>
                {" "}
                ${plan.monthly_spending_limit}
            </strong>
        </li>
    )}

    {plan.badge && (
        <li>
            🏷 Badge :
            <strong> {plan.badge}</strong>
        </li>
    )}

    {plan.recommended && (
        <li className="font-semibold text-green-600">
            ⭐ Recommended Plan
        </li>
    )}

    {Object.entries(plan.features || {}).map(([key, value]) =>
        value ? (
            <li key={key}>
                ✔ {key.replaceAll("_", " ")}
            </li>
        ) : null
    )}

</ul>




            <button
                onClick={() => handlePurchaseClick(plan)}
                className="w-full rounded-lg bg-indigo-600 py-3 text-white hover:bg-indigo-700"
            >
                Purchase Now
            </button>
        </div>
    ))}
</div>

                {/* ✅ NEW PAYMENT METHOD SELECTION MODAL */}
            {showPaymentModal && selectedPlan && (
                <PaymentMethodModal
                    plan={selectedPlan}
                    onClose={() => setShowPaymentModal(false)}
                />
            )}
        </div>
    )
}

