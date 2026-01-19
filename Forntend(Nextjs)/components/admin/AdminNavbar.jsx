'use client'
import Link from "next/link"
import { useRouter } from "next/navigation"
import { LogOut, ChevronDown } from "lucide-react"
import { useState } from "react"
import useUser from "../../hooks/useUser"

const AdminNavbar = () => {
    const { user, isAuthenticated, loading ,isAdmin} = useUser()
    const [open, setOpen] = useState(false)
    const router = useRouter()

    if (loading) {
        return <div className="px-12 py-4">Loading...</div>
    }

    const handleLogout = () => {
        // clear context
        localStorage.removeItem("Token")
        localStorage.removeItem("RefreshToken")
        router.push("/auth/login")
    }

    return (
        <div className="flex items-center justify-between px-12 py-3 border-b border-slate-200 bg-white">
            
            {/* LEFT: LOGO */}
            <Link href="/" className="relative text-3xl font-semibold text-slate-700">
                <span className="text-green-600">go</span>cart
                <span className="text-green-600 text-4xl">.</span>

                {isAdmin && (
                    <span className="absolute -top-1 -right-12 text-xs px-2 py-0.5 rounded-full bg-green-500 text-white">
                        Admin
                    </span>
                )}
            </Link>

            {/* RIGHT: USER */}
            <div className="relative">
                {isAuthenticated ? (
                    <button
                        onClick={() => setOpen(!open)}
                        className="flex items-center gap-2 text-slate-700 hover:bg-slate-100 px-3 py-1.5 rounded-md"
                    >
                        <span>
                            Hi, <strong>{user?.first_name}</strong>
                        </span>
                        <ChevronDown size={16} />
                    </button>
                ) : (
                    <span>Hi, Guest</span>
                )}

                {/* DROPDOWN */}
                {open && (
                    <div className="absolute right-0 mt-2 w-40 bg-white border rounded-md shadow-md z-50">
                        <Link
                            href="/admin"
                            className="block px-4 py-2 text-sm hover:bg-slate-100"
                        >
                            Profile
                        </Link>

                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                        >
                            <LogOut size={16} />
                            Logout
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}

export default AdminNavbar
