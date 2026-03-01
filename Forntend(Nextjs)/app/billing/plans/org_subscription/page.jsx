'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import AxiosInstance from '@/api/AxiosInstance'
import Loading from '@/components/Loading'
import PaymentMethodModal from '@/components/billing/PaymentMethodModal'

export default function OrganizationSubscriptionPage() {
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
            const res = await AxiosInstance.get(
                '/api/billing/org-plans/',
                { useTenant: true }
            )
            setPlans(res.data)
        } catch (err) {
            toast.error('Failed to load subscription plans')
        } finally {
            setLoading(false)
        }
    }

    const handlePurchaseClick = (plan) => {
        setSelectedPlan(plan)
        setShowPaymentModal(true)
    }

    const handlePaymentSuccess = () => {
        toast.success('Organization subscription activated successfully!')
        router.push('/dashboard')
    }

    if (loading) return <Loading />

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <h1 className="text-3xl font-bold text-center mb-12 text-gray-800">
                Choose an Organization Plan
            </h1>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                {plans
                    .filter(plan => plan.plan_type === 'organization')
                    .map(plan => (
                        <div
                            key={plan.id}
                            className="bg-white rounded-xl shadow-lg p-6 flex flex-col items-center hover:scale-105 transition"
                        >
                            <h2 className="text-2xl font-semibold mb-4">
                                {plan.name}
                            </h2>

                            <p className="text-4xl font-bold mb-2 text-indigo-600">
                                ${plan.price}
                            </p>

                            <p className="text-sm text-gray-500 mb-6">
                                {plan.billing_cycle}
                            </p>

                            <ul className="text-left mb-8 space-y-2">
                                <li>👥 Max Users: {plan.max_users}</li>
                                <li>📦 Max Products: {plan.max_products}</li>
                                <li>💾 Storage: {plan.storage_gb} GB</li>

                                {Object.entries(plan.features || {}).map(
                                    ([key, value]) =>
                                        value && (
                                            <li key={key}>
                                                ✅ {key.replace('_', ' ').toUpperCase()}
                                            </li>
                                        )
                                )}
                            </ul>

                            <button
                                onClick={() => handlePurchaseClick(plan)}
                                className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                            >
                                Activate Plan
                            </button>
                        </div>
                    ))}
            </div>

            {showPaymentModal && selectedPlan && (
                <PaymentMethodModal
                    plan={selectedPlan}
                    onClose={() => setShowPaymentModal(false)}
                    onSuccess={handlePaymentSuccess}
                />
            )}
        </div>
    )
}