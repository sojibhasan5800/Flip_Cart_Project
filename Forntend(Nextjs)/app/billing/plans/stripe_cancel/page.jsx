'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function StripeCancelPage() {
    const router = useRouter()

    useEffect(() => {
        const timer = setTimeout(() => {
            router.push('/billing/plans') // Back to plans page
        }, 4000)
        return () => clearTimeout(timer)
    }, [])

    return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gray-50 p-6">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
                <h1 className="text-3xl font-bold text-red-600 mb-4">❌ Payment Cancelled</h1>
                <p className="text-gray-700 mb-6">You have cancelled the payment or it failed.</p>
                <button
                    onClick={() => router.push('/billing/plans')}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                >
                    Try Again
                </button>
                <p className="text-gray-500 text-sm mt-4">Redirecting to Plans page in 4 seconds...</p>
            </div>
        </div>
    )
}