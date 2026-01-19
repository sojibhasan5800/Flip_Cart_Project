'use client'
import Image from "next/image"
import { MapPin, Mail, Phone } from "lucide-react"

const StoreInfo = ({store}) => {
    const logo =
        store?.store_logo && store.store_logo !== ""
            ? store.store_logo
            : "/assets/gs_logo.jpg"

    const status = store.is_verified
        ? "approved"
        : store.is_active
        ? "pending"
        : "rejected"
    return (
        <div className="flex-1 space-y-2 text-sm">
            <Image width={100} height={100} src={logo} alt={store.business_name || "Unknown Store"} className="max-w-20 max-h-20 object-contain shadow rounded-full max-sm:mx-auto" />
            <div className="flex flex-col sm:flex-row gap-3 items-center">
                <h3 className="text-xl font-semibold text-slate-800"> {store.business_name || "Unknown Store"} </h3>
                <span className="text-sm">@{store.username || "unknown"}</span>

                {/* Status Badge */}
                <span
                    className={`text-xs font-semibold px-4 py-1 rounded-full ${status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : status === 'rejected'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-green-100 text-green-800'
                        }`}
                >
                    {status}
                </span>
            </div>

            <p className="text-slate-600 my-5 max-w-2xl">{store.store_description}</p>
            <p className="flex items-center gap-2"> <MapPin size={16} /> {store.address_line1}</p>
            <p className="flex items-center gap-2"><Phone size={16} /> {store.phone}</p>
            <p className="flex items-center gap-2"><Mail size={16} />  {store.business_email}</p>
            <p className="text-slate-700 mt-5">Applied  on <span className="text-xs">{new Date(store.created_at).toLocaleDateString()}</span> by</p>
            <div className="flex items-center gap-2 text-sm ">
                <Image 
                    width={36} 
                    height={36} 
                    src={store.user?.profile_picture || "/assets/default_user.jpg"} 
                    alt={store.user?.first_name || "User"} 
                    className="w-9 h-9 rounded-full" 
                    />

                <div>
                    <p className="text-slate-600 font-medium">{store.user?.full_name || "Unknown User"}</p>
                    <p className="text-slate-400">{store.user?.email || "No email"}</p>
                </div>
            </div>
        </div>
    )
}

export default StoreInfo