'use client'
import { assets } from "@/assets/assets"
import { useEffect, useState } from "react"
import Image from "next/image"
import toast from "react-hot-toast"
import Loading from "@/components/Loading"
import useAuth from '../../../hooks/useAuth'
import useToken  from "../../../hooks/useToken"
import AxiosInstance from "../../../api/AxiosInstance"
import { useImageKitUpload} from "../../../hooks/useImageKitUpload";

import { useRouter } from "next/navigation"
import { set } from "date-fns"


export default function CreateStore() {
    const { isAuthenticated } = useAuth()
    const router = useRouter()
    const {token} = useToken()
    const [alreadySubmitted, setAlreadySubmitted] = useState(false)
    const [status, setStatus] = useState("")
    const [loading, setLoading] = useState(true)
    const [message, setMessage] = useState("")

    const [storeInfo, setStoreInfo] = useState({
        business_name: "",
        username: "",
        store_description: "",
        email: "",
        contact: "",
        address: "",
        image: null,
    })
    // Use custom upload hook
  const { uploadFile, url: imageUrl, loading: uploadLoading, error: uploadError, progress } = useImageKitUpload();
    // Handler for form input changes
    const onChangeHandler = (e) => {
        setStoreInfo({ ...storeInfo, [e.target.name]: e.target.value })
    }

    const fetchSellerStatus = async () => {
        // Logic to check if the store is already submitted
        // const token = getToken
        try {
            const { data } = await AxiosInstance.get("api/merchant_user/merchant/store/create",);
            console.log(data.status)
            if (['pending', 'approved', 'rejected'].includes(data.status)) {
                setStatus(data.status)
                setAlreadySubmitted(true)
                switch (data.status) {
                    case"approved":
                        setMessage("Your store has been approved! Redirecting to your dashboard...");
                        setTimeout(() => {
                            router.push('/store')
                        }, 5000);
                        break;
                    case"pending":
                        setMessage("Your store application is under review. You will be notified once it's approved.");
                        break;
                    case"rejected":
                        setMessage("Unfortunately, your store application was rejected. Please contact support for more information.");
                        break;
                    default:
                        break;
            }
    
        }else {
                setAlreadySubmitted(false)
            }
    }
    catch (error) { 
        toast.error(error.response?.data?.error || "Failed to fetch store status.")
    }
    setLoading(false)
}

    const onSubmitHandler = async (e) => {
        e.preventDefault()

        // Logic to submit the store details
        if (!isAuthenticated) {
            toast.error("You must be logged in to create a store.")
            router.push('/auth/login')
            return
        }
    try {
        let storeLogoUrl = '';
        if (storeInfo.image) {
                // Upload image using hook
                storeLogoUrl = await uploadFile(storeInfo.image, { folder: '/stores/', tags: ['logo'] });
                if (uploadError) throw new Error(uploadError);  // Handle upload error
                toast.success(`Upload complete: ${progress}% - URL: ${storeLogoUrl}`);
            }

        const formData = new FormData();
        formData.append("store_logo", storeLogoUrl);
        formData.append("username", storeInfo.username);
        formData.append("business_name", storeInfo.business_name);
        formData.append("store_description", storeInfo.store_description);
        formData.append("business_email", storeInfo.email);
        formData.append("phone", storeInfo.contact);
        formData.append("address_line1", storeInfo.address);
        const {data} = await AxiosInstance.post("api/merchant_user/merchant/store/create/", formData,);
        toast.success(data.message || "Store details submitted successfully.")
        await fetchSellerStatus();
        

    }catch (error) {
        toast.error(data.error || "Failed to submit store details.")
        console.error("Store submission error:", error);
    }

}
    useEffect(() => {
        if (isAuthenticated){

            fetchSellerStatus()
        }
    }, [isAuthenticated])

    if (! isAuthenticated) {
        return (<div className="min-h-[80vh] flex flex-col items-center justify-center">
            <h1 className="sm:text-2xl lg:text-3xl mx-5 font-semibold text-slate-500 text-center max-w-2xl">please <span className="text-slate-500">login</span>to continue</h1>
        </div>
        )
    }

    return !loading ? (
        <>
            {!alreadySubmitted ? (
                <div className="mx-6 min-h-[70vh] my-16">
                    <form onSubmit={e => toast.promise(onSubmitHandler(e), { loading: "Submitting data..." })} className="max-w-7xl mx-auto flex flex-col items-start gap-3 text-slate-500">
                        {/* Title */}
                        <div>
                            <h1 className="text-3xl ">Add Your <span className="text-slate-800 font-medium">Store</span></h1>
                            <p className="max-w-lg">To become a seller on GoCart, submit your store details for review. Your store will be activated after admin verification.</p>
                        </div>

                        <label className="mt-10 cursor-pointer">
                            Store Logo
                            <Image src={storeInfo.image ? URL.createObjectURL(storeInfo.image) : assets.upload_area} className="rounded-lg mt-2 h-16 w-auto" alt="" width={150} height={100} />
                            <input type="file" accept="image/*" onChange={(e) => setStoreInfo({ ...storeInfo, image: e.target.files[0] })} hidden />
                        </label>

                        <p>Username</p>
                        <input name="username" onChange={onChangeHandler} value={storeInfo.username} type="text" placeholder="Enter your store username" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded" />

                        <p>Business Name</p>
                        <input name="business_name" onChange={onChangeHandler} value={storeInfo.business_name} type="text" placeholder="Enter your store business_name" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded" />

                        <p>Store Description</p>
                        <textarea name="store_description" onChange={onChangeHandler} value={storeInfo.store_description} rows={5} placeholder="Enter your store store_description" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded resize-none" />

                        <p>Email</p>
                        <input name="email" onChange={onChangeHandler} value={storeInfo.email} type="email" placeholder="Enter your store email" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded" />

                        <p>Contact Number</p>
                        <input name="contact" onChange={onChangeHandler} value={storeInfo.contact} type="text" placeholder="Enter your store contact number" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded" />

                        <p>Address</p>
                        <textarea name="address" onChange={onChangeHandler} value={storeInfo.address} rows={5} placeholder="Enter your store address" className="border border-slate-300 outline-slate-400 w-full max-w-lg p-2 rounded resize-none" />

                        <button className="bg-slate-800 text-white px-12 py-2 rounded mt-10 mb-40 active:scale-95 hover:bg-slate-900 transition ">Submit</button>
                    </form>
                </div>
            ) : (
                <div className="min-h-[80vh] flex flex-col items-center justify-center">
                    <p className="sm:text-2xl lg:text-3xl mx-5 font-semibold text-slate-500 text-center max-w-2xl">{message}</p>
                    {status === "approved" && <p className="mt-5 text-slate-400">redirecting to dashboard in <span className="font-semibold">5 seconds</span></p>}
                </div>
            )}
        </>
    ) : (<Loading />)
}