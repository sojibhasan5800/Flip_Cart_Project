'use client'
import { useEffect, useState } from "react"
import Loading from "../Loading"                  // Your Loading component
import Link from "next/link"
import { ArrowRightIcon } from "lucide-react"
import SellerNavbar from "./StoreNavbar"
import SellerSidebar from "./StoreSidebar"
import { useRouter } from "next/navigation"

import AxiosInstance from "../../api/AxiosInstance"
import toast from "react-hot-toast"               // Using toast — if not installed, import it

const StoreLayout = ({ children }) => {
    const router = useRouter()
    const [isSeller, setIsSeller] = useState(false)
    const [loading, setLoading] = useState(true)
    const [storeInfo, setStoreInfo] = useState(null)
    const [statusMessage, setStatusMessage] = useState("")
    
    // New part — for multiple store selector
    const [showStoreSelector, setShowStoreSelector] = useState(false)
    const [possibleStores, setPossibleStores] = useState([])

 
const fetchSellerStatus = async () => {
    try {
        setLoading(true)

        const { data } = await AxiosInstance.get(
            "/api/merchant_user/seller-status/"
        )

        console.log("Seller status response:", data)

        // ✅ CASE 1: single approved store → DIRECT dashboard
        if (
            data.is_seller === true &&
            data.status === "approved" &&
            Array.isArray(data.possible_stores) &&
            data.possible_stores.length === 1
        ) {
            const store = data.possible_stores[0]

            // save active store
            localStorage.setItem(
                "ORGANIZATION_DOMAIN",
                store.store_url.replace(/^https?:\/\//, "")
            )
            localStorage.setItem("ACTIVE_BUSINESS_EMAIL", store.business_email)
            localStorage.setItem("ACTIVE_ORG_ID", store.org_id)
           
            setIsSeller(true)
            setStoreInfo(store)
            setShowStoreSelector(false)
            router.replace("/store")
            return
        }

        //  CASE 2: multiple stores → show selector
        if (data.status === "multiple_stores") {
            setPossibleStores(data.possible_stores || [])
            setShowStoreSelector(true)
            return
        }

        //  CASE 3: pending / rejected / no_store
        setStatusMessage(data.message || "Access restricted")

    } catch (error) {
        console.error("Seller status error:", error)
        toast.error("Failed to check store status")
        setStatusMessage("Server error. Please try again.")
    } finally {
        setLoading(false)
    }
}

        const handleSelectStore = (store) => {
        localStorage.setItem(
            "ORGANIZATION_DOMAIN",
            store.store_url.replace(/^https?:\/\//, "")
        )
        localStorage.setItem("ACTIVE_ORG_ID", store.org_id)
        localStorage.setItem("ACTIVE_BUSINESS_EMAIL", store.business_email)

        setStoreInfo(store)
        setIsSeller(true)
        setShowStoreSelector(false)
        router.replace("/store")

        toast.success(`Store selected: ${store.business_name}`)
        }


useEffect(() => {
    const initializeSeller = async () => {
        setLoading(true);

        const activeOrgId = localStorage.getItem("ACTIVE_ORG_ID");

        try {
            const { data } = await AxiosInstance.get("/api/merchant_user/seller-status/");

            console.log("Full seller-status response:", data); // ← এটা দেখো console-এ

            // Step 1: যদি active org থাকে → validate করো
            if (activeOrgId) {
                const found = data.possible_stores?.find(
                    s => String(s.org_id) === String(activeOrgId) && s.status === "approved"
                );

                if (found) {
                    console.log("Active org is valid → using it directly");
                    setStoreInfo(found);
                    setIsSeller(true);
                    setShowStoreSelector(false);
                    setLoading(false);
                    return; // ← এখান থেকে বেরিয়ে যাও, আর কিছু চেক করার দরকার নেই
                }

                // invalid হলে ক্লিয়ার করো
                console.warn("Active org not found or not approved → clearing localStorage");
                localStorage.removeItem("ACTIVE_ORG_ID");
                localStorage.removeItem("ORGANIZATION_DOMAIN");
                localStorage.removeItem("ACTIVE_BUSINESS_EMAIL");
            }

            // Step 2: active org না থাকলে বা invalid হলে → backend logic অনুসারে হ্যান্ডেল
            if (data.is_seller === true && data.status === "approved") {
                // single store case (backend থেকে approved এসেছে)
                if (data.possible_stores?.length === 1) {
                    const store = data.possible_stores[0];
                    localStorage.setItem("ORGANIZATION_DOMAIN", store.store_url.replace(/^https?:\/\//, ""));
                    localStorage.setItem("ACTIVE_BUSINESS_EMAIL", store.business_email);
                    localStorage.setItem("ACTIVE_ORG_ID", store.org_id);

                    setStoreInfo(store);
                    setIsSeller(true);
                    setShowStoreSelector(false);
                    // router.replace("/store"); // optional — যদি চাও
                }
            } 
            else if (data.status === "multiple_stores") {
                // multiple stores → selector দেখাও
                setPossibleStores(data.possible_stores.filter(s => s.status === "approved") || []);
                setShowStoreSelector(true);
            } 
            else {
                // no_store / pending / rejected
                setStatusMessage(data.message || "Access restricted");
                setIsSeller(false);
                setShowStoreSelector(false);
            }

        } catch (error) {
            console.error("Seller init error:", error);
            toast.error("Failed to load seller status");
            setStatusMessage("Server error. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    initializeSeller();
}, []);

    if (loading) {
        return <Loading />
    }

    // Unauthorized / pending / rejected state
    if (!isSeller && !showStoreSelector) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center text-center px-6">
                <h1 className="text-2xl sm:text-4xl font-semibold text-slate-400">
                    Seller Dashboard Access Restricted
                </h1>
                <p className="mt-4 text-slate-500 max-w-md">
                    {statusMessage}
                </p>
                <Link 
                    href="/" 
                    className="bg-slate-700 text-white flex items-center gap-2 mt-8 p-3 px-8 rounded-full hover:bg-slate-800 transition"
                >
                    Go to home <ArrowRightIcon size={18} />
                </Link>
            </div>
        )
    }

    return (
        <>
            {/* Multiple Store Selector Modal */}
            {showStoreSelector && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl p-6 sm:p-8 max-w-lg w-full max-h-[90vh] overflow-y-auto">
                        <h2 className="text-2xl font-bold mb-6 text-center">
                            Select Your Stores
                        </h2>
                        
                        <div className="space-y-4">
                            {possibleStores.map((store) => (
                          <button
                                key={store.business_email}
                                onClick={() => store.status === "approved" && handleSelectStore(store)}
                                disabled={store.status !== "approved"}
                                className={`w-full p-4 border rounded-lg transition flex items-center gap-4 text-left
                                    ${
                                        store.status === "approved"
                                            ? "hover:bg-blue-50 cursor-pointer"
                                            : "bg-gray-100 opacity-60 cursor-not-allowed"
                                    }
                                `}
                            >

                                    {store.store_logo ? (
                                        <img 
                                            src={store.store_logo} 
                                            alt={store.business_name}
                                            className="w-14 h-14 rounded-full object-cover border"
                                        />
                                    ) : (
                                        <div className="w-14 h-14 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                                            No Logo
                                        </div>
                                    )}
                                    
                                    <div>
                                        <div className="font-semibold text-lg">
                                            {store.business_name}
                                        </div>
                                        <div className="text-sm text-gray-600">
                                            {store.business_email}
                                        </div>
                                        {store.status !== "approved" && (
                                            <div className="text-xs text-amber-600 mt-1">
                                                {store.status === "pending" ? "(Pending)" : "(Rejected)"}
                                            </div>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>

                        <div className="mt-8 text-center text-sm text-gray-500">
                            Please select the store you want to manage
                        </div>
                    </div>
                </div>
            )}

            {/* Main Seller Dashboard Layout */}
            <div className="flex flex-col h-screen">
                <SellerNavbar />
                <div className="flex flex-1 items-start h-full overflow-y-scroll no-scrollbar">
                    <SellerSidebar storeInfo={storeInfo} />
                    <div className="flex-1 h-full p-5 lg:pl-12 lg:pt-12 overflow-y-scroll">
                        {children}
                    </div>
                </div>
            </div>
        </>
    )
}

export default StoreLayout
