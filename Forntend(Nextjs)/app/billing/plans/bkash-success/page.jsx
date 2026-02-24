'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import AxiosInstance from '@/api/AxiosInstance'
import { toast } from 'react-hot-toast'

export default function BkashSuccessPage() {
    const router = useRouter()
    const searchParams = useSearchParams()

    useEffect(() => {
        const verifyPayment = async () => {
            const paymentID = searchParams.get('paymentID')
            if (!paymentID) {
                toast.error("Invalid payment")
                router.push('/billing/plans')
                return
            }

            try {
                await AxiosInstance.post(
                    '/api/payments/webhook/',
                    { bkash: true, paymentID },
                    { useTenant: true }
                )
                toast.success("Plan purchased with bKash! Boost products now.")
                router.push('/store/manage-product')
            } catch (err) {
                toast.error("Verification failed")
                router.push('/billing/plans')
            }
        }
        verifyPayment()
    }, [searchParams, router])

    return <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <h1 className="text-2xl font-bold text-gray-800">Verifying Payment...</h1>
    </div>
}