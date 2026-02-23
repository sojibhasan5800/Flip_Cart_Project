'use client'

import { useEffect, useState } from "react"
import { toast } from "react-hot-toast"
import Image from "next/image"
import Loading from "@/components/Loading"
import useUser from '../../../hooks/useUser'
import AxiosInstance from '../../../api/AxiosInstance'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'

// Stripe publishable key
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)

export default function StoreManageProducts() {
    const currency = process.env.NEXT_PUBLIC_CURRENCY_SYMBOL || '৳'
    const [loading, setLoading] = useState(true)
    const [products, setProducts] = useState([])
    const [pendingToggle, setPendingToggle] = useState(null)
    const [pendingBoost, setPendingBoost] = useState(null)
    const [subscriptionInfo, setSubscriptionInfo] = useState(null)
    const [showPaymentModal, setShowPaymentModal] = useState(false)
    const [selectedProduct, setSelectedProduct] = useState(null)
    const { user } = useUser()

    // Fetch products + active boosting subscription info
    const fetchProductsAndSubscription = async () => {
        try {
            // 1. Products
            const prodRes = await AxiosInstance.get(
                "/api/merchant_user/merchant-products/",
                {
                    useTenant: true,
                    params: { organization_id: localStorage.getItem("ACTIVE_ORG_ID") }
                }
            )
            setProducts(
                prodRes.data.data.sort(
                    (a, b) => new Date(b.created_date) - new Date(a.created_date)
                )
            )

            // 2. Active subscriptions (বুস্টিং প্ল্যান খুঁজব)
            const subRes = await AxiosInstance.get("/api/billing/subscriptions/", { useTenant: true })
            const activeBoostSub = subRes.data.find(
                sub => sub.status === 'active' && sub.plan?.plan_type === 'boosting'
            )

            if (activeBoostSub) {
                setSubscriptionInfo({
                    plan_name: activeBoostSub.plan.name,
                    max_boosted: activeBoostSub.plan.max_boosted_products || 0,
                    current_boosted: activeBoostSub.boosted_products_count || 0,
                    can_boost_more: activeBoostSub.boosted_products_count < (activeBoostSub.plan.max_boosted_products || 0),
                    subscription_id: activeBoostSub.id  // পেমেন্টের জন্য দরকার
                })
            } else {
                setSubscriptionInfo(null)
            }

        } catch (error) {
            console.error(error)
            toast.error("Failed to load products or subscription info")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (user) {
            fetchProductsAndSubscription()
        }
    }, [user])

    const toggleStock = async (productId) => {
        // ... আপনার আগের লজিক একই রাখুন (এখানে পরিবর্তন নেই) ...
        setPendingToggle(productId)
        try {
            const { data } = await AxiosInstance.patch(
                `/api/merchant_user/products/toggle-stock/${productId}/`,
                null,
                { useTenant: true }
            )
            setProducts(prev =>
                prev.map(p =>
                    p.id === productId ? { ...p, is_available: data.is_available } : p
                )
            )
            toast.success("Stock status updated")
        } catch (error) {
            toast.error("Failed to toggle stock")
        } finally {
            setPendingToggle(null)
        }
    }

    const handleBoostClick = (product) => {
        if (!subscriptionInfo) {
            toast.error("You need an active boosting plan. Please purchase one from Plans page.")
            // Optional: router.push('/dashboard/billing/plans')
            return
        }
        if (!subscriptionInfo.can_boost_more) {
            toast.error("Boost limit reached for your current plan. Upgrade your plan.")
            return
        }

        setSelectedProduct(product)
        setShowPaymentModal(true)
    }

    const handlePaymentSuccess = (boostedProductId) => {
        setProducts(prev =>
            prev.map(p =>
                p.id === boostedProductId
                    ? { ...p, is_boosted: true, boost_remaining_days: 30 }
                    : p
            )
        )
        fetchProductsAndSubscription() // Refresh limit
        toast.success("Product boosted successfully!")
        setShowPaymentModal(false)
    }

    if (loading) return <Loading />

    return (
        <>
            <h1 className="text-2xl text-slate-500 mb-5">
                Manage <span className="text-slate-800 font-medium">Products</span>
            </h1>

            {subscriptionInfo ? (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-blue-800">
                        <strong>{subscriptionInfo.plan_name}</strong> Plan • 
                        Boost slots: {subscriptionInfo.current_boosted} / {subscriptionInfo.max_boosted}
                        {subscriptionInfo.can_boost_more ? (
                            <span className="ml-2 text-green-600 font-medium"> • Available</span>
                        ) : (
                            <span className="ml-2 text-red-600 font-medium"> • Limit reached</span>
                        )}
                    </p>
                </div>
            ) : (
                <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-yellow-800">
                        No active boosting plan. <a href="/dashboard/billing/plans" className="underline font-medium">Purchase a plan</a> to boost products.
                    </p>
                </div>
            )}

            <table className="w-full max-w-5xl text-left ring ring-slate-200 rounded overflow-hidden text-sm">
                <thead className="bg-slate-50 text-gray-700 uppercase tracking-wider">
                    <tr>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3 hidden md:table-cell">Description</th>
                        <th className="px-4 py-3 hidden md:table-cell">MRP</th>
                        <th className="px-4 py-3">Price</th>
                        <th className="px-4 py-3">Stock</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Boost</th>
                    </tr>
                </thead>

                <tbody className="text-slate-700">
                    {products.map(product => {
                        const isOutOfStock = product.stock === 0
                        const isAvailable = product.is_available
                        const isPending = pendingToggle === product.id
                        const isBoosted = product.is_boosted

                        return (
                            <tr key={product.id} className="border-t border-gray-200 hover:bg-gray-50">
                                <td className="px-4 py-3">
                                    <div className="flex gap-2 items-center">
                                        <Image
                                            width={40}
                                            height={40}
                                            className="p-1 shadow rounded"
                                            src={product.images || "/placeholder-product.jpg"}
                                            alt={product.product_name}
                                        />
                                        {product.product_name}
                                    </div>
                                </td>
                                <td className="px-4 py-3 max-w-md text-slate-600 hidden md:table-cell truncate">
                                    {product.description}
                                </td>
                                <td className="px-4 py-3 hidden md:table-cell">
                                    {currency} {product.mrp?.toLocaleString() || "—"}
                                </td>
                                <td className="px-4 py-3">
                                    {currency} {product.price.toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-center">
                                    {product.stock}
                                </td>
                                <td className="px-4 py-3 text-center">
                                    {/* Toggle switch – আপনার আগের কোড */}
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="sr-only peer"
                                            checked={isAvailable}
                                            onChange={() => {
                                                if (isOutOfStock) {
                                                    toast("Cannot enable — stock is 0", { icon: "⚠️" })
                                                    return
                                                }
                                                if (!isPending) toggleStock(product.id)
                                            }}
                                            disabled={isOutOfStock || isPending}
                                        />
                                        <div
                                            className={`w-9 h-5 rounded-full transition-colors duration-200
                                                ${isOutOfStock ? "bg-gray-300 cursor-not-allowed" 
                                                : isAvailable ? "bg-green-600" : "bg-slate-300"} 
                                                peer peer-checked:bg-green-600`}
                                        ></div>
                                        <span
                                            className={`dot absolute left-1 top-1 w-3 h-3 bg-white rounded-full transition-transform duration-200 ease-in-out
                                                ${isAvailable ? "translate-x-4" : ""}`}
                                        ></span>
                                    </label>
                                </td>

                                <td className="px-4 py-3 text-center">
                                    {isBoosted ? (
                                        <div className="text-green-600 font-medium">
                                            Boosted
                                            {product.boost_remaining_days && (
                                                <span className="block text-xs text-gray-500">
                                                    {product.boost_remaining_days} days left
                                                </span>
                                            )}
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => handleBoostClick(product)}
                                            disabled={pendingBoost === product.id || !subscriptionInfo?.can_boost_more}
                                            className={`px-3 py-1.5 text-sm font-medium rounded-md transition
                                                ${subscriptionInfo?.can_boost_more 
                                                    ? "bg-indigo-600 hover:bg-indigo-700 text-white" 
                                                    : "bg-gray-400 cursor-not-allowed text-gray-700"}`}
                                        >
                                            {pendingBoost === product.id ? "Boosting..." : "Boost"}
                                        </button>
                                    )}
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>

            {showPaymentModal && selectedProduct && (
                <PaymentModal
                    product={selectedProduct}
                    subscriptionId={subscriptionInfo?.subscription_id}
                    onClose={() => setShowPaymentModal(false)}
                    onSuccess={handlePaymentSuccess}
                />
            )}
        </>
    )
}

// Payment Modal
function PaymentModal({ product, subscriptionId, onClose, onSuccess }) {
    const [gateway, setGateway] = useState('stripe')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const stripe = useStripe()
    const elements = useElements()

    const handleBoostPayment = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            const payload = {
                gateway,
                amount: 500, // Boost price – আপনি চাইলে ডায়নামিক করুন (plan থেকে আনুন)
                currency: gateway === 'bkash' ? 'BDT' : 'USD',
                boost_product_id: product.id,
                organization_subscription: subscriptionId  // বিলিং-এ লিঙ্ক করার জন্য
            }

            const res = await AxiosInstance.post(
                '/api/payments/create-intent/',
                payload,
                { useTenant: true }
            )

            if (gateway === 'stripe') {
                const { client_secret } = res.data

                const { error: stripeErr } = await stripe.confirmCardPayment(client_secret, {
                    payment_method: {
                        card: elements.getElement(CardElement),
                        billing_details: { name: `Boost ${product.product_name}` }
                    }
                })

                if (stripeErr) {
                    setError(stripeErr.message)
                    return
                }

                onSuccess(product.id)

            } else if (gateway === 'bkash') {
                const { bkash_url } = res.data
                window.location.href = bkash_url  // bKash পেমেন্ট পেজে যাবে
            }

        } catch (err) {
            setError(err?.response?.data?.error || "Payment failed")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <h2 className="text-xl font-semibold mb-4">
                    Boost: {product.product_name}
                </h2>

                <form onSubmit={handleBoostPayment}>
                    <div className="mb-4">
                        <label className="block text-sm font-medium mb-1">Pay with</label>
                        <select
                            value={gateway}
                            onChange={e => setGateway(e.target.value)}
                            className="w-full border rounded px-3 py-2"
                        >
                            <option value="stripe">Card (Stripe)</option>
                            <option value="bkash">bKash</option>
                        </select>
                    </div>

                    {gateway === 'stripe' && (
                        <div className="mb-6 p-3 border rounded bg-gray-50">
                            <CardElement options={{ style: { base: { fontSize: '16px' } } }} />
                        </div>
                    )}

                    {error && <p className="text-red-600 mb-4 text-sm">{error}</p>}

                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border rounded text-gray-700 hover:bg-gray-100"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`px-5 py-2 rounded text-white font-medium ${loading ? "bg-indigo-400" : "bg-indigo-600 hover:bg-indigo-700"}`}
                        >
                            {loading ? "Processing..." : `Boost for ${currency}500`}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}