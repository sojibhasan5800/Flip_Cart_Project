'use client'

import { usePathname } from "next/navigation"
import { HomeIcon, ShieldCheckIcon, StoreIcon, TicketPercentIcon } from "lucide-react"
import Image from "next/image"
import Link from "next/link"
import useUser from "../../hooks/useUser"

const AdminSidebar = () => {

    const pathname = usePathname()
    const {user} = useUser()
    const profileImage = user?.profile?.profile_picture || "/assets/gs_logo.jpg"
    const fullName = user? `${user.first_name} ${user.last_name}`: "Admin"
    
 const sidebarLinks = [
    {
        title: "Dashboard",
        links: [
            { name: "Overview", href: "/admin", icon: HomeIcon },
        ]
    },
    {
        title: "Store Management",
        links: [
            { name: "Stores", href: "/admin/stores", icon: StoreIcon },
            { name: "Approve Stores", href: "/admin/approve", icon: ShieldCheckIcon },
        ]
    },
    {
        title: "Subscriptions",
        links: [
            { name: "Subscription Plans", href: "/admin/subscription-plans", icon: TicketPercentIcon },
            { name: "Organization Subscriptions", href: "/admin/org-subscriptions", icon: TicketPercentIcon },
        ]
    },
    {
        title: "Boosting",
        links: [
            { name: "Active Boosts", href: "/admin/boosts", icon: TicketPercentIcon },
        ]
    },
    {
        title: "Billing",
        links: [
            { name: "Invoices", href: "/admin/invoices", icon: TicketPercentIcon },
        ]
    },
]

    return (
        <div className="inline-flex h-full flex-col gap-5 border-r border-slate-200 sm:min-w-60">
            <div className="flex flex-col gap-3 justify-center items-center pt-8 max-sm:hidden">
                <Image className="w-14 h-14 rounded-full" src={profileImage} alt="" width={80} height={80} />
                <p className="text-slate-700">   Hi, {fullName}</p>
            </div>

        <div className="max-sm:mt-6">
                {sidebarLinks.map((group, gIndex) => (
                    <div key={gIndex} className="mb-2">
                    {/* Group title */}
                    <p className="text-slate-400 text-xs uppercase px-3 mb-1">{group.title}</p>

                    {/* Group links */}
                    {group.links.map((link, index) => (
                        <Link
                        key={index}
                        href={link.href}   // এখন ঠিকভাবে string আছে
                        className={`relative flex items-center gap-3 text-slate-500 hover:bg-slate-50 p-2.5 transition 
                            ${pathname === link.href ? 'bg-slate-100 sm:text-slate-600' : ''}`}
                        >
                        <link.icon size={18} className="sm:ml-5" />
                        <p className="max-sm:hidden">{link.name}</p>
                        {pathname === link.href && (
                            <span className="absolute bg-green-500 right-0 top-1.5 bottom-1.5 w-1 sm:w-1.5 rounded-l"></span>
                        )}
                        </Link>
                    ))}
                    </div>
                ))}
                </div>
        </div>
    )
}

export default AdminSidebar