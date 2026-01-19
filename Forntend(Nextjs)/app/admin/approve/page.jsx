'use client'
import { storesDummyData } from "@/assets/assets"
import StoreInfo from "@/components/admin/StoreInfo"
import Loading from "@/components/Loading"
import { useEffect, useState } from "react"
import toast from "react-hot-toast"
import useUser from '../../../hooks/useUser'
import  AxiosInstance  from "../../../api/AxiosInstance";

export default function AdminApprove() {

    const {user,isAuthenticated} = useUser()
    const [stores, setStores] = useState([])
    const [loading, setLoading] = useState(true)


    const fetchStores = async () => {
        try{
            const {data} = await AxiosInstance.get("api/admin_core/store-approval/?status=pending")
            setStores(data.data)
            console.log(data)
        }
        catch(error){
           toast.error(error?.response?.data?.error || "Error fetching stores")
            
        }
        setLoading(false)
    }

    const handleApprove = async ({ storeId, status }) => {
        try {
            let response;

            if (status === "approved") {
                // APPROVE → POST
                response = await AxiosInstance.post(
                    "api/admin_core/store-approval/",
                    { storeId }
                );
            } 
            else if (status === "rejected") {
                // REJECT → PUT
                response = await AxiosInstance.put(
                    "api/admin_core/store-approval/",
                    {  storeId }
                );
            }

            toast.success(response?.data?.message || "Store updated successfully");
            await fetchStores();

        } catch (error) {
            toast.error(error?.response?.data?.error || "Error updating store");
            console.log(error)
        }
    };


    useEffect(() => {
        if (isAuthenticated) {
            fetchStores()
        }
    }, [isAuthenticated])

    return !loading ? (
        <div className="text-slate-500 mb-28">
            <h1 className="text-2xl">Approve <span className="text-slate-800 font-medium">Stores</span></h1>

            {stores.length ? (
                <div className="flex flex-col gap-4 mt-4">
                    {stores.map((store) => (
                        <div key={store.id} className="bg-white border rounded-lg shadow-sm p-6 flex max-md:flex-col gap-4 md:items-end max-w-4xl" >
                            {/* Store Info */}
                            <StoreInfo store={store} />
                            

                            {/* Actions */}
                            <div className="flex gap-3 pt-2 flex-wrap">
                                <button onClick={() => toast.promise(handleApprove({ storeId: store.id, status: 'approved' }), { loading: "approving" })} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm" >
                                    Approve
                                </button>
                                <button onClick={() => toast.promise(handleApprove({ storeId: store.id, status: 'rejected' }), { loading: 'rejecting' })} className="px-4 py-2 bg-slate-500 text-white rounded hover:bg-slate-600 text-sm" >
                                    Reject
                                </button>
                            </div>
                        </div>
                    ))}

                </div>) : (
                <div className="flex items-center justify-center h-80">
                    <h1 className="text-3xl text-slate-400 font-medium">No Application Pending</h1>
                </div>
            )}
        </div>
    ) : <Loading />
}