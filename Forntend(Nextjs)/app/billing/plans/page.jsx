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

export default function BillingPlansPage() {
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
            const res = await AxiosInstance.get('/api/billing/product-boosts/', { useTenant: true })
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
        <div className="min-h-screen bg-gray-50 p-8">
            <h1 className="text-3xl font-bold text-center mb-12 text-gray-800">Choose Your Boosting Plan</h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {plans.filter(plan => plan.plan_type === 'product_boost').map(plan => (
                    <div 
                        key={plan.id} 
                        className={`bg-white rounded-xl shadow-lg p-6 flex flex-col items-center transform hover:scale-105 transition duration-300 ${
                            plan.level === 'enterprise' ? 'border-4 border-indigo-500' : ''
                        }`}
                    >
                        <h2 className="text-2xl font-semibold mb-4 text-gray-800">{plan.name}</h2>
                        <p className="text-4xl font-bold mb-2 text-indigo-600">${plan.price}</p>
                        <p className="text-sm text-gray-500 mb-6">{plan.billing_cycle}</p>

                        <ul className="text-left mb-8 space-y-2">
                            <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Max Boosted Products: {plan.max_boosted_products}</li>
                            <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Storage: {plan.storage_gb} GB</li>
                            <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Max Users: {plan.max_users}</li>
                            {/* Features from JSON */}
                            {Object.entries(plan.features).map(([key, value]) => value && (
                                <li key={key} className="flex items-center gap-2"><span className="text-green-500">✓</span> {key.replace('_', ' ').toUpperCase()}</li>
                            ))}
                        </ul>

                        <button 
                            onClick={() => handlePurchaseClick(plan)}
                            className="w-full py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition"
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

