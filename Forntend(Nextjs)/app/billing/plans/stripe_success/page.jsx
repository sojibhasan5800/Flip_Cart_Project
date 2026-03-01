'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import AxiosInstance from '@/api/AxiosInstance'
import { toast } from 'react-hot-toast'
import Loading from '@/components/Loading'

export default function StripeSuccessPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const [loading, setLoading] = useState(true)

    const session_id = searchParams.get('session_id')
    const plan_type = searchParams.get('plan_type')

    useEffect(() => {
        if (!session_id) return

        const confirmPayment = async () => {
            try {
                // const res = await AxiosInstance.post(
                //     '/api/billing/plans/confirm-payment/',
                //     { session_id },
                //     { useTenant: true }
                // )
                toast.success('Payment successful! Your plan is activated.')
                    setTimeout(() => {
                    if (plan_type === 'organization') {
                        router.push('/store')
                    } else if (plan_type === 'boost') {
                        router.push('/store/manage-product')
                    } else {
                        router.push('/')
                    }
                    }, 2000)
            } catch (err) {
                toast.error('Payment verified failed. Contact support.')
                setLoading(false)
            }
        }

        confirmPayment()
    }, [session_id])

    if (loading) return <Loading />

    return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gray-50 p-6">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
                <h1 className="text-3xl font-bold text-green-600 mb-4">🎉 Payment Successful!</h1>
                <p className="text-gray-700 mb-6">Your subscription has been activated.</p>
                <p className="text-gray-500 text-sm mb-6">Redirecting to {plan_type === 'organization' ? 'Dashboard' : plan_type === 'boost' ? 'Manage Products' : 'Home'}...</p>
            </div>
        </div>
    )
}