'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import AxiosInstance from '@/api/AxiosInstance'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import Loading from '@/components/Loading'

// Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)

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
            const res = await AxiosInstance.get('/api/billing/plans/', { useTenant: true })
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
                {plans.filter(plan => plan.plan_type === 'boosting').map(plan => (
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

            {showPaymentModal && selectedPlan && (
                <PaymentModal 
                    plan={selectedPlan} 
                    onClose={() => setShowPaymentModal(false)} 
                    onSuccess={handlePaymentSuccess} 
                />
            )}
        </div>
    )
}

// Payment Modal (A to Z payment processing)
function PaymentModal({ plan, onClose, onSuccess }) {
    const [gateway, setGateway] = useState('stripe')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const stripe = useStripe()
    const elements = useElements()

    const handlePlanPayment = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            const payload = {
                gateway,
                amount: plan.price,
                currency: gateway === 'bkash' ? 'BDT' : plan.currency,
                plan_slug: plan.slug  // Backend to link plan
            }

            const res = await AxiosInstance.post(
                '/api/billing/plans/purchase/',
                payload,
                { useTenant: true }
            )

            if (gateway === 'stripe') {
                const { client_secret } = res.data
                const { error: stripeErr } = await stripe.confirmCardPayment(client_secret, {
                    payment_method: {
                        card: elements.getElement(CardElement),
                        billing_details: { name: `Purchase ${plan.name}` }
                    }
                })

                if (stripeErr) {
                    setError(stripeErr.message)
                    return
                }

                onSuccess(plan.id)

            } else if (gateway === 'bkash') {
                const { bkash_url } = res.data
                window.location.href = bkash_url
            }

        } catch (err) {
            setError(err?.response?.data?.error || "Payment failed. Try again.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl">
                <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Purchase {plan.name} Plan</h2>

                <form onSubmit={handlePlanPayment}>
                    <div className="mb-6">
                        <label className="block text-sm font-medium mb-2 text-gray-700">Payment Method</label>
                        <select
                            value={gateway}
                            onChange={e => setGateway(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:border-indigo-500"
                        >
                            <option value="stripe">Credit/Debit Card (Stripe)</option>
                            <option value="bkash">bKash Mobile Wallet</option>
                        </select>
                    </div>

                    {gateway === 'stripe' && (
                        <div className="mb-6 p-4 border border-gray-300 rounded-lg bg-gray-50">
                            <label className="block text-sm font-medium mb-2 text-gray-700">Card Details</label>
                            <CardElement options={{ style: { base: { fontSize: '16px', color: '#424770', '::placeholder': { color: '#aab7c4' } } } }} />
                        </div>
                    )}

                    <div className="text-center mb-6">
                        <p className="text-xl font-semibold text-indigo-600">${plan.price} / {plan.billing_cycle}</p>
                    </div>

                    {error && <p className="text-red-500 mb-4 text-center text-sm">{error}</p>}

                    <div className="flex justify-between gap-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`flex-1 py-3 rounded-lg text-white font-medium transition ${loading ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                        >
                            {loading ? 'Processing...' : 'Pay Now'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}