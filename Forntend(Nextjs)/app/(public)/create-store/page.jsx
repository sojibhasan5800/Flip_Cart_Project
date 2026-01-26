
'use client'
import { assets } from "@/assets/assets"
import { useEffect, useState } from "react"
import Image from "next/image"
import toast from "react-hot-toast"
import Loading from "@/components/Loading"
import useAuth from '../../../hooks/useAuth'
import useToken from "../../../hooks/useToken"
import AxiosInstance from "../../../api/AxiosInstance"
import { useImageKitUpload } from "../../../hooks/useImageKitUpload"
import { useRouter } from "next/navigation"

export default function CreateStore() {
    const { isAuthenticated } = useAuth()
    const router = useRouter()
    const { token } = useToken()
    const [loading, setLoading] = useState(true)
    const [stores, setStores] = useState([])
    const [storeInfo, setStoreInfo] = useState({
        business_name: "",
        username: "",
        store_description: "",
        email: "",
        contact: "",
        address: "",
        image: null,
    })
    const { uploadFile, loading: uploadLoading, error: uploadError, progress } = useImageKitUpload()

    // Input change handler
    const onChangeHandler = (e) => {
        setStoreInfo({ ...storeInfo, [e.target.name]: e.target.value })
    }

    // Fetch all stores of the user
    const fetchStores = async () => {
        try {
            setLoading(true)
            const { data } = await AxiosInstance.get("api/merchant_user/seller-status/")
            if (data.status === "approved") {
                // // Only one approved store → redirect immediately
                // localStorage.setItem(
                //     "ORGANIZATION_DOMAIN",
                //     data.possible_stores.store_url.replace(/^https?:\/\//, "")
                // )
                // localStorage.setItem("ACTIVE_STORE_NAME", data.possible_stores.business_name)
                // localStorage.setItem("ACTIVE_ORG_ID", data.possible_stores.org_id)
                setStores(data.possible_stores)
                // router.push("/store")
            } else if (data.status === "multiple_stores") {
                setStores(data.possible_stores)
            } else if (data.status === "pending") {
                setStores(data.possible_stores || [])
            } else if (data.status === "no_store") {
                setStores([])
            }
        } catch (err) {
            toast.error("Failed to fetch store info.")
        } finally {
            setLoading(false)
        }
    }

    // Submit new store
    const onSubmitHandler = async (e) => {
        e.preventDefault()
        if (!isAuthenticated) {
            toast.error("You must be logged in to create a store.")
            router.push("/auth/login")
            return
        }

        try {
            let storeLogoUrl = ''
            if (storeInfo.image) {
                storeLogoUrl = await uploadFile(storeInfo.image, { folder: '/stores/', tags: ['logo'] })
                if (uploadError) throw new Error(uploadError)
            }

            const formData = new FormData()
            formData.append("store_logo", storeLogoUrl)
            formData.append("username", storeInfo.username)
            formData.append("business_name", storeInfo.business_name)
            formData.append("store_description", storeInfo.store_description)
            formData.append("business_email", storeInfo.email)
            formData.append("phone", storeInfo.contact)
            formData.append("address_line1", storeInfo.address)

            const { data } = await AxiosInstance.post("api/merchant_user/merchant/store/create/", formData)
            toast.success(data.message || "Store submitted successfully")
            fetchStores() // Refresh store list
        } catch (error) {
            toast.error(error.response?.data?.error || "Failed to submit store")
        }
    }

    useEffect(() => {
        if (isAuthenticated) fetchStores()
    }, [isAuthenticated])

    if (!isAuthenticated) {
        return (
            <div className="min-h-[80vh] flex flex-col items-center justify-center">
                <h1 className="sm:text-2xl lg:text-3xl mx-5 font-semibold text-slate-500 text-center max-w-2xl">
                    Please <span className="text-slate-800">login</span> to continue
                </h1>
            </div>
        )
    }

    if (loading) return <Loading />

    return (
        <div className="max-w-7xl mx-auto px-6 my-16">
            <h1 className="text-3xl font-semibold mb-4">Your Stores</h1>
            <p className="text-slate-500 mb-8">Manage all your stores. You can create new stores or select existing ones.</p>

            {/* Stores list */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
                {stores.length > 0 ? stores.map((store) => (
                    <div
                        key={store.business_email}
                        className={`border rounded-lg p-6 transition transform hover:scale-105 ${
                            store.status === "approved"
                                ? "border-green-400 shadow-lg"
                                : store.status === "pending"
                                    ? "border-yellow-400 opacity-80"
                                    : "border-red-400 opacity-60"
                        }`}
                    >
                        <div className="flex flex-col items-center">
                            <div className="w-24 h-24 rounded-full overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center shadow-sm">
                            <Image
                                src={store.store_logo || assets.upload_area}
                                alt={store.business_name}
                                width={96}
                                height={96}
                                className="object-cover w-full h-full"
                            />
                        </div>

                            <h2 className="text-lg font-medium">{store.business_name}</h2>
                            <p className={`mt-1 text-sm font-semibold ${
                                store.status === "approved"
                                    ? "text-green-600"
                                    : store.status === "pending"
                                        ? "text-yellow-600"
                                        : "text-red-600"
                            }`}>{store.status.toUpperCase()}</p>
                            {store.status === "approved" && (
                                <button
                                    className="mt-3 bg-green-600 text-white px-4 py-1 rounded hover:bg-green-700 transition"
                                    onClick={() => {
                                        if (!store.store_url) {
                                            toast.error("Store URL not available yet")
                                            return
                                        }

                                        localStorage.setItem(
                                            "ORGANIZATION_DOMAIN",
                                            store.store_url.replace(/^https?:\/\//, "")
                                        )
                                        localStorage.setItem("ACTIVE_STORE_NAME", store.business_name)
                                        localStorage.setItem("ACTIVE_ORG_ID", store.org_id)
                                        router.push("/store")
}}

                                >
                                    Go to Dashboard
                                </button>
                            )}
                        </div>
                    </div>
                )) : (
                    <p className="text-slate-500 col-span-full text-center">No stores found. Create a new store below.</p>
                )}
            </div>

            {/* Create new store form */}
            <div className="border-t pt-8">
                <h2 className="text-2xl font-semibold mb-4">Add New Store</h2>
                <form onSubmit={onSubmitHandler} className="flex flex-col gap-4 max-w-xl">
                    <label className="cursor-pointer">
                        Store Logo
                        <Image
                            src={storeInfo.image ? URL.createObjectURL(storeInfo.image) : assets.upload_area}
                            width={150}
                            height={100}
                            className="rounded-lg mt-2"
                            alt=""
                        />
                        <input type="file" accept="image/*" hidden onChange={e => setStoreInfo({ ...storeInfo, image: e.target.files[0] })} />
                    </label>

                    <input
                        type="text"
                        name="username"
                        placeholder="Store Username"
                        value={storeInfo.username}
                        onChange={onChangeHandler}
                        className="border p-2 rounded"
                        required
                    />
                    <input
                        type="text"
                        name="business_name"
                        placeholder="Business Name"
                        value={storeInfo.business_name}
                        onChange={onChangeHandler}
                        className="border p-2 rounded"
                        required
                    />
                    <textarea
                        name="store_description"
                        rows={3}
                        placeholder="Store Description"
                        value={storeInfo.store_description}
                        onChange={onChangeHandler}
                        className="border p-2 rounded resize-none"
                        required
                    />
                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        value={storeInfo.email}
                        onChange={onChangeHandler}
                        className="border p-2 rounded"
                        required
                    />
                    <input
                        type="text"
                        name="contact"
                        placeholder="Contact Number"
                        value={storeInfo.contact}
                        onChange={onChangeHandler}
                        className="border p-2 rounded"
                        required
                    />
                    <textarea
                        name="address"
                        rows={3}
                        placeholder="Address"
                        value={storeInfo.address}
                        onChange={onChangeHandler}
                        className="border p-2 rounded resize-none"
                        required
                    />
                    <button type="submit" className="bg-slate-800 text-white py-2 px-6 rounded hover:bg-slate-900 transition">
                        {uploadLoading ? `Uploading... ${progress}%` : "Submit Store"}
                    </button>
                </form>
            </div>
        </div>
    )
}


