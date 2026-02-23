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
                toast.error("Invalid payment response")
                router.push('/store/manage-product')
                return
            }

            try {
                await AxiosInstance.post(
                    '/api/payments/webhook/',
                    { bkash: true, paymentID },
                    { useTenant: true }
                )

                toast.success("bKash payment successful! Product boosted.")
                router.push('/store/manage-product?boost=success')
            } catch (err) {
                console.error(err)
                toast.error("Payment verification failed. Please contact support.")
                router.push('/store/manage-product?boost=failed')
            }
        }

        verifyPayment()
    }, [searchParams, router])

    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
                <h1 className="text-2xl font-bold mb-4">Verifying your bKash payment...</h1>
                <p className="text-gray-600">Please wait a moment.</p>
            </div>
        </div>
    )
}