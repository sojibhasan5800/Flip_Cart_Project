'use client'
import { useEffect, useState } from "react"
import { toast } from "react-hot-toast"
import Image from "next/image"
import Loading from "@/components/Loading"
import useUser from '../../../hooks/useUser'
import AxiosInstance from '../../../api/AxiosInstance'

export default function StoreManageProducts() {
    const currency = process.env.NEXT_PUBLIC_CURRENCY_SYMBOL || '$'
    const [loading, setLoading] = useState(true)
    const [products, setProducts] = useState([])
    const [pendingToggle, setPendingToggle] = useState(null)
    const { user } = useUser()

    const fetchProducts = async () => {
        try {
            const { data } = await AxiosInstance.get(
                "/api/merchant_user/merchant-products/",
                {
                    useTenant: true,
                    params: {
                        organization_id: localStorage.getItem("ACTIVE_ORG_ID")
                    }
                }
            );
            setProducts(
                data.data.sort(
                    (a, b) => new Date(b.created_date) - new Date(a.created_date)
                )
            );
        } catch (error) {
            toast.error(
                error?.response?.data?.error || "Failed to fetch products"
            );
        } finally {
            setLoading(false);
        }
    };


    const toggleStock = async (productId) => {
        setPendingToggle(productId)  // ✅ mark: start pending
        try {
            const { data } = await AxiosInstance.patch(
                `/api/merchant_user/products/toggle-stock/${productId}/`,
                null,
                {
                    useTenant: true,
                    params: {
                        organization_id: localStorage.getItem("ACTIVE_ORG_ID")
                    }
                }
            )
            console.log("data", data)

            // ✅ mark: set backend truth only
            setProducts(prev =>
                prev.map(p =>
                    p.id === productId
                        ? { ...p, is_available: data.is_available }
                        : p
                )
            )

            toast.success("Stock status updated successfully")
        } catch (error) {
            toast.error(error?.response?.data?.error || "Failed to toggle stock")
        } finally {
            setPendingToggle(null)  // ✅ mark: finish pending
        }
    }
    useEffect(() => {
        if (user) {
            fetchProducts();
        }
    }, [user]);

    if (loading) return <Loading />;

    return (
        <>
            <h1 className="text-2xl text-slate-500 mb-5">
                Manage <span className="text-slate-800 font-medium">Products</span>
            </h1>

            <table className="w-full max-w-4xl text-left ring ring-slate-200 rounded overflow-hidden text-sm">
                    <thead className="bg-slate-50 text-gray-700 uppercase tracking-wider">
                        {/* Stock column (optional) */}
                        <tr>
                            <th className="px-4 py-3">Name</th>
                            <th className="px-4 py-3 hidden md:table-cell">Description</th>
                            <th className="px-4 py-3 hidden md:table-cell">MRP</th>
                            <th className="px-4 py-3">Price</th>
                            <th className="px-4 py-3">Stock</th>
                            <th className="px-4 py-3">Status</th>
                        </tr>
                    </thead>

                <tbody className="text-slate-700">
                    {products.map(product => {
                        const isOutOfStock = product.stock === 0
                        const isAvailable = product.is_available
                        const isPending = pendingToggle === product.id  // ✅ mark: pending per row

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
                                                if (!isPending) toggleStock(product.id)  // ✅ mark: prevent multi-click
                                            }}
                                            disabled={isOutOfStock || isPending}  // ✅ mark: disable while pending
                                        />
                                        
                                        <div
                                            className={`w-9 h-5 rounded-full transition-colors duration-200
                                                ${isOutOfStock 
                                                    ? "bg-gray-300 cursor-not-allowed" 
                                                    : isAvailable 
                                                        ? "bg-green-600" 
                                                        : "bg-slate-300"} 
                                                peer peer-checked:bg-green-600`}
                                        ></div>
                                        <span
                                            className={`dot absolute left-1 top-1 w-3 h-3 bg-white rounded-full transition-transform duration-200 ease-in-out
                                                ${isAvailable ? "translate-x-4" : ""}`}
                                        ></span>
                                    </label>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </>
    );
}