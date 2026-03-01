'use client'
import Loading from "@/components/Loading"
import { CircleDollarSignIcon, ShoppingBasketIcon, StarIcon, TagsIcon } from "lucide-react"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { useEffect, useState ,useCallback} from "react"
import toast from "react-hot-toast"
import AxiosInstance from "../../api/AxiosInstance" 
import DashboardLive from '@/components/store/DashboardLive'
import SubscriptionBanner from '@/components/billing/SubscriptionBanner'


export default function Dashboard() {

    const currency = process.env.NEXT_PUBLIC_CURRENCY_SYMBOL || '$'

    const router = useRouter()

    const [loading, setLoading] = useState(true)
    const [dashboardData, setDashboardData] = useState({
        totalProducts: 0,
        totalEarnings: 0,
        totalOrders: 0,
        ratings: [],
    })


    const dashboardCardsData = [
        { title: 'Total Products', value: dashboardData.totalProducts, icon: ShoppingBasketIcon },
        { title: 'Total Earnings', value: currency + dashboardData.totalEarnings, icon: CircleDollarSignIcon },
        { title: 'Total Orders', value: dashboardData.totalOrders, icon: TagsIcon },
        { title: 'Total Ratings', value: dashboardData.ratings.length, icon: StarIcon },
    ]
    const orgId = localStorage.getItem('ACTIVE_ORG_ID')


    const fetchDashboardData = async () => {
        if (!orgId) {
        toast.error("No active store selected")
        setLoading(false)
        return
        }
        try{
            const {data} = await AxiosInstance.get("api/merchant_user/seller-store-dashboard/",{ useTenant: true })
            setDashboardData(data.dashboardData)
            console.log("Fetched dashboard data:", data.dashboardData)
            
        }
        catch(error){
            toast.error(error?.response?.data?.error || "Error fetching dashboard data")
        }
        setLoading(false)
    }

        // -------------------------------
  // ✅ Changed this: wrap handleLiveUpdate with useCallback to prevent infinite toast
  const handleLiveUpdate = useCallback((newData) => {
    setDashboardData(prev => ({
      ...prev,
      ...newData
    }))
    toast.success("Dashboard updated live!", { duration: 2000 })
  }, [])  // ✅ dependency empty array


  //   const handleLiveUpdate = (newData) => {
  //   setDashboardData((prev) => ({
  //     ...prev,
  //     ...newData,
  //     // ratings array merge করতে চাইলে এখানে logic দিতে পারো
  //     // উদাহরণ: ratings: newData.recentReviews || prev.ratings
  //   }))
  //   toast.success("Dashboard updated live!", { duration: 2000 })
  // }


    useEffect(() => {
        fetchDashboardData()
    }, [orgId])

    if (loading) return <Loading />

    return (
    <div className="text-slate-500 mb-28">
      <h1 className="text-2xl">
        Seller <span className="text-slate-800 font-medium">Dashboard</span>
      </h1>
      <SubscriptionBanner
  trialEndsAt={dashboardData.trial_ends_at}
  isTrial={dashboardData.is_trial}
  hasActiveSubscription={dashboardData.has_active_subscription}
/>
      {/* Live update */}
      {orgId && <DashboardLive orgId={orgId} onUpdate={handleLiveUpdate} />}  // ✅ useCallback applied

      {/* Cards */}
      <div className="flex flex-wrap gap-5 my-10 mt-4">
        {dashboardCardsData.map((card, index) => (
          <div
            key={index}
            className="flex items-center gap-11 border border-slate-200 p-3 px-6 rounded-lg"
          >
            <div className="flex flex-col gap-3 text-xs">
              <p>{card.title}</p>
              <b className="text-2xl font-medium text-slate-700">{card.value}</b>
            </div>
            <card.icon
              size={50}
              className="w-11 h-11 p-2.5 text-slate-400 bg-slate-100 rounded-full"
            />
          </div>
        ))}
      </div>

      {/* Recent Reviews */}
      <h2 className="text-xl font-medium mt-10 mb-4">Recent Reviews</h2>

      <div className="mt-5">
        {dashboardData.ratings?.length > 0 ? (
          dashboardData.ratings.map((review, index) => (
            <div
              key={index}
              className="flex max-sm:flex-col gap-5 sm:items-center justify-between py-6 border-b border-slate-200 text-sm text-slate-600 max-w-4xl"
            >
              <div>
                <div className="flex gap-3">
                  <Image
                    src={review.user?.image || "/default-avatar.png"}
                    alt=""
                    className="w-10 aspect-square rounded-full"
                    width={40}
                    height={40}
                  />
                  <div>
                    <p className="font-medium">{review.user?.name || "Anonymous"}</p>
                    <p className="font-light text-slate-500">
                      {new Date(review.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <p className="mt-3 text-slate-500 max-w-xs leading-6">{review.review}</p>
              </div>

              <div className="flex flex-col justify-between gap-6 sm:items-end">
                <div className="flex flex-col sm:items-end">
                  <p className="text-slate-400">{review.product?.category}</p>
                  <p className="font-medium">{review.product?.name}</p>
                  <div className="flex items-center">
                    {Array(5)
                      .fill('')
                      .map((_, starIndex) => (
                        <StarIcon
                          key={starIndex}
                          size={17}
                          className="text-transparent mt-0.5"
                          fill={review.rating >= starIndex + 1 ? "#00C950" : "#D1D5DB"}
                        />
                      ))}
                  </div>
                </div>

                {review.product?.id && (
                  <button
                    onClick={() => router.push(`/product/${review.product.id}`)}
                    className="bg-slate-100 px-5 py-2 hover:bg-slate-200 rounded transition-all"
                  >
                    View Product
                  </button>
                )}
              </div>
            </div>
          ))
        ) : (
          <p className="text-slate-400">No recent reviews yet.</p>
        )}
      </div>
    </div>
  )


}
