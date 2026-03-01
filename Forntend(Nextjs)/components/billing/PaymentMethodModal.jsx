'use client'

import Image from 'next/image'
import { useState } from 'react'
import AxiosInstance from '@/api/AxiosInstance'
import { toast } from 'react-hot-toast'

export default function PaymentMethodModal({ plan, onClose }) {
    const [gateway, setGateway] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleContinue = async () => {
        if (!gateway) {
            toast.error('Please select a payment method')
            return
        }

        setLoading(true)
        try {
            const res = await AxiosInstance.post(
                '/api/payments/plans/purchase-plan/',
                {
                    plan_slug: plan.slug,
                    gateway: gateway,
                    plan_type: plan.plan_type
                },
                { useTenant: true }
            )

            window.location.href = res.data.redirect_url
        } catch (err) {
            toast.error('Failed to initiate payment')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-8 w-full max-w-md shadow-xl">
                <h2 className="text-2xl font-bold text-center mb-6">
                    Choose Payment Method
                </h2>

                <div className="space-y-4">
                    {/* Stripe */}
                    <div
                        onClick={() => setGateway('stripe')}
                        className={`border rounded-xl p-4 cursor-pointer flex items-center gap-4 ${
                            gateway === 'stripe' ? 'border-indigo-600 bg-indigo-50' : ''
                        }`}
                    >
                        <Image src="/payments/stripe.svg" width={40} height={40} alt="Stripe" />
                        <div>
                            <p className="font-semibold">Stripe</p>
                            <p className="text-sm text-gray-500">
                                Visa, Mastercard, International Cards
                            </p>
                        </div>
                    </div>

                    {/* SSLCommerz */}
                    <div
                        onClick={() => setGateway('sslcommerz')}
                        className={`border rounded-xl p-4 cursor-pointer flex items-center gap-4 ${
                            gateway === 'sslcommerz' ? 'border-green-600 bg-green-50' : ''
                        }`}
                    >
                        <Image src="/payments/sslcommerz.png" width={40} height={40} alt="SSLCommerz" />
                        <div>
                            <p className="font-semibold">SSLCommerz</p>
                            <p className="text-sm text-gray-500">
                                bKash, Nagad, Rocket, Cards
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-8 flex gap-4">
                    <button
                        onClick={onClose}
                        className="flex-1 border rounded-lg py-3 hover:bg-gray-100"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleContinue}
                        disabled={loading}
                        className="flex-1 bg-indigo-600 text-white rounded-lg py-3 hover:bg-indigo-700"
                    >
                        {loading ? 'Redirecting...' : 'Continue'}
                    </button>
                </div>
            </div>
        </div>
    )
}