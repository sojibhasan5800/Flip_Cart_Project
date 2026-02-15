

'use client'
import Loading from "@/components/Loading"
import OrdersAreaChart from "@/components/OrdersAreaChart"
import DashboardSchedulerToggle from "@/components/admin/DashboardSchedulerToggle"
import { CircleDollarSignIcon, ShoppingBasketIcon, StoreIcon, TagsIcon } from "lucide-react"
import { useEffect, useState } from "react"
import toast from "react-hot-toast";
import AxiosInstance from "../../api/AxiosInstance" 

export default function AdminDashboard() {

    const currency = process.env.NEXT_PUBLIC_CURRENCY_SYMBOL || '$'

    const [loading, setLoading] = useState(true)
    const [dashboardData, setDashboardData] = useState({
        products: 0,
        revenue: 0,
        orders: 0,
        stores: 0,
        allOrders: [],
    })

    const dashboardCardsData = [
        { title: 'Total Products', value: dashboardData.products, icon: ShoppingBasketIcon },
        { title: 'Total Revenue', value: currency + dashboardData.revenue, icon: CircleDollarSignIcon },
        { title: 'Total Orders', value: dashboardData.orders, icon: TagsIcon },
        { title: 'Total Stores', value: dashboardData.stores, icon: StoreIcon },
    ]

    const fetchDashboardData = async () => {
        try{
        const {data} = await AxiosInstance.get("api/admin_core/dashboard/super-admin/",{ useTenant: true })
            setDashboardData({
            products: data.cards.products,
            revenue: data.cards.revenue,
            orders: data.cards.orders,
            stores: data.cards.stores,
            allOrders: data.allOrders,
        })
            
        }
        catch(error){
            toast.error(error?.response?.data?.error || "Error fetching dashboard data")
        }
        setLoading(false)
    }

    useEffect(() => {
        fetchDashboardData()
    }, [])

    if (loading) return <Loading />

    return (
        <div className="text-slate-500 space-y-10">
           <div>
        <h1 className="text-2xl font-semibold text-slate-800">
          Admin <span className="text-slate-600">Dashboard</span>
        </h1>
        <p className="text-slate-500 mt-1">Platform overview & real-time controls</p>
      </div>
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-medium text-slate-800 mb-4 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500 inline-block"></span>
            Real-time Dashboard Updates
            </h2>
            
            {/* Toggle কম্পোনেন্ট */}
            <DashboardSchedulerToggle />
            
            <p className="text-sm text-slate-500 mt-3">
            Controls automatic stats push for online merchants every 1 minute.
            Turning this off will pause all real-time updates to reduce server load.
            </p>
        </div>

            {/* Cards */}
            <div className="flex flex-wrap gap-5 my-10 mt-4">
                {
                    dashboardCardsData.map((card, index) => (
                        <div key={index} className="flex items-center gap-10 border border-slate-200 p-3 px-6 rounded-lg">
                            <div className="flex flex-col gap-3 text-xs">
                                <p>{card.title}</p>
                                <b className="text-2xl font-medium text-slate-700">{card.value}</b>
                            </div>
                            <card.icon size={50} className=" w-11 h-11 p-2.5 text-slate-400 bg-slate-100 rounded-full" />
                        </div>
                    ))
                }
            </div>

            {/* Area Chart */}
            <OrdersAreaChart allOrders={dashboardData.allOrders} />
        </div>
    )
}