'use client'

import { useEffect, useState } from "react"
import AxiosInstance from "@/api/AxiosInstance"
import {
    Crown,
    Users,
    Package,
    HardDrive,
    CheckCircle2,
    XCircle,
    Calendar,
    RefreshCw
} from "lucide-react"

export default function BillingPage() {

    const [loading, setLoading] = useState(true)
    const [subscriptionData, setSubscriptionData] = useState(null)

    useEffect(() => {
        fetchSubscription()
    }, [])

    const fetchSubscription = async () => {
        try {
            const res = await AxiosInstance.get(
                "api/billing/current-subscription/"
            )

            setSubscriptionData(res.data)

        } catch (error) {
            console.error(error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-10">
                <div className="animate-pulse space-y-4">
                    <div className="h-10 bg-gray-200 rounded w-64"></div>
                    <div className="h-40 bg-gray-200 rounded-2xl"></div>
                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="h-28 bg-gray-200 rounded-xl"></div>
                        <div className="h-28 bg-gray-200 rounded-xl"></div>
                        <div className="h-28 bg-gray-200 rounded-xl"></div>
                    </div>
                </div>
            </div>
        )
    }

    if (!subscriptionData?.has_subscription) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-10">

                <h1 className="text-3xl font-bold">
                    Billing & Payments
                </h1>

                <div className="mt-8 bg-white border rounded-2xl p-10 text-center">

                    <Crown
                        size={50}
                        className="mx-auto text-gray-400"
                    />

                    <h2 className="text-xl font-semibold mt-4">
                        No Active Subscription
                    </h2>

                    <p className="text-gray-500 mt-2">
                        Upgrade your account to unlock premium features.
                    </p>

                    <button
                        className="mt-6 px-5 py-2 rounded-lg bg-green-600 text-white"
                    >
                        View Plans
                    </button>

                </div>

            </div>
        )
    }

    const subscription = subscriptionData.subscription
    const plan = subscriptionData.plan

    return (
        <div className="max-w-7xl mx-auto px-4 py-10">

            {/* Header */}

            <div>

                <h1 className="text-3xl font-bold">
                    Billing & Payments
                </h1>

                <p className="text-gray-500 mt-2">
                    Manage your subscription and billing information
                </p>

            </div>

            {/* Current Plan */}

            <div className="mt-8 bg-white border rounded-2xl p-6 shadow-sm">

                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

                    <div className="flex items-center gap-4">

                        <div className="w-12 h-12 rounded-xl bg-yellow-100 flex items-center justify-center">
                            <Crown className="text-yellow-600" />
                        </div>

                        <div>

                            <h2 className="text-xl font-semibold">
                                {plan.name}
                            </h2>

                            <p className="text-gray-500">
                                {plan.billing_cycle}
                            </p>

                        </div>

                    </div>

                    <div className="text-right">

                        <div
                            className={`inline-flex px-4 py-1 rounded-full text-sm text-white ${
                                subscription.status === "active"
                                    ? "bg-green-600"
                                    : "bg-red-500"
                            }`}
                        >
                            {subscription.status}
                        </div>

                        <p className="text-3xl font-bold mt-3">
                            ${plan.price}
                        </p>

                    </div>

                </div>

            </div>

            {/* Usage Cards */}

            <div className="grid md:grid-cols-3 gap-5 mt-6">

                <div className="bg-white border rounded-xl p-5">

                    <div className="flex items-center justify-between">

                        <Package />

                        <span className="text-sm text-gray-500">
                            Max Products
                        </span>

                    </div>

                    <h3 className="text-3xl font-bold mt-4">
                        {plan.max_products}
                    </h3>

                </div>

                <div className="bg-white border rounded-xl p-5">

                    <div className="flex items-center justify-between">

                        <Users />

                        <span className="text-sm text-gray-500">
                            Team Members
                        </span>

                    </div>

                    <h3 className="text-3xl font-bold mt-4">
                        {plan.max_users}
                    </h3>

                </div>

                <div className="bg-white border rounded-xl p-5">

                    <div className="flex items-center justify-between">

                        <HardDrive />

                        <span className="text-sm text-gray-500">
                            Storage
                        </span>

                    </div>

                    <h3 className="text-3xl font-bold mt-4">
                        {plan.storage_gb} GB
                    </h3>

                </div>

            </div>

            {/* Subscription Details */}

            <div className="grid lg:grid-cols-2 gap-6 mt-6">

                <div className="bg-white border rounded-2xl p-6">

                    <h3 className="font-semibold text-lg mb-5">
                        Subscription Details
                    </h3>

                    <div className="space-y-4">

                        <div className="flex justify-between">

                            <span className="text-gray-500">
                                Plan Level
                            </span>

                            <span className="font-medium capitalize">
                                {plan.plan_level}
                            </span>

                        </div>

                        <div className="flex justify-between">

                            <span className="text-gray-500">
                                Billing Cycle
                            </span>

                            <span className="font-medium capitalize">
                                {plan.billing_cycle}
                            </span>

                        </div>

                        <div className="flex justify-between">

                            <span className="text-gray-500">
                                Start Date
                            </span>

                            <span>
                                {new Date(
                                    subscription.start_date
                                ).toLocaleDateString()}
                            </span>

                        </div>

                        <div className="flex justify-between">

                            <span className="text-gray-500">
                                End Date
                            </span>

                            <span>
                                {subscription.end_date
                                    ? new Date(
                                          subscription.end_date
                                      ).toLocaleDateString()
                                    : "Unlimited"}
                            </span>

                        </div>

                    </div>

                </div>

                {/* Auto Renew */}

                <div className="bg-white border rounded-2xl p-6">

                    <h3 className="font-semibold text-lg mb-5">
                        Renewal Settings
                    </h3>

                    <div className="flex items-center gap-3">

                        <RefreshCw size={20} />

                        <div>

                            <p className="font-medium">
                                Auto Renew
                            </p>

                            <p className="text-sm text-gray-500">
                                {subscription.auto_renew
                                    ? "Your subscription renews automatically."
                                    : "Auto renewal is disabled."}
                            </p>

                        </div>

                    </div>

                </div>

            </div>

            {/* Features */}

            <div className="bg-white border rounded-2xl p-6 mt-6">

                <h3 className="font-semibold text-lg mb-6">
                    Included Features
                </h3>

                <div className="grid md:grid-cols-2 gap-4">

                    {Object.entries(plan.features || {}).map(
                        ([key, value]) => (
                            <div
                                key={key}
                                className="flex items-center justify-between border rounded-lg p-3"
                            >

                                <span className="capitalize">
                                    {key.replaceAll("_", " ")}
                                </span>

                                {value ? (
                                    <CheckCircle2
                                        className="text-green-600"
                                        size={20}
                                    />
                                ) : (
                                    <XCircle
                                        className="text-red-500"
                                        size={20}
                                    />
                                )}

                            </div>
                        )
                    )}

                </div>

            </div>

            {/* Actions */}

            <div className="flex flex-wrap gap-4 mt-8">

                <button
                    className="px-5 py-3 rounded-xl bg-green-600 text-white font-medium"
                >
                    Upgrade Plan
                </button>

                <button
                    className="px-5 py-3 rounded-xl border font-medium"
                >
                    Manage Subscription
                </button>

            </div>

        </div>
    )
}