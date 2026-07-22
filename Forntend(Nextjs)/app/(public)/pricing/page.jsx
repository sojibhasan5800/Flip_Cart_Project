
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
                <li>Duration : {plan.duration_days} Days</li>

                {Object.entries(plan.features || {}).map(([key, value]) =>
                    value ? (
                        <li key={key}>
                            ✓ {key.replace(/_/g, " ")}
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

