"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, Building2, LogOut, User } from "lucide-react";
import { useState, useEffect } from "react";
import useUser from "../../hooks/useUser";
import AxiosInstance from "../../api/AxiosInstance";
import toast from "react-hot-toast";

const StoreNavbar = () => {
  const { user, isAuthenticated, loading } = useUser();
  const [open, setOpen] = useState(false);
  const [stores, setStores] = useState([]);
  const router = useRouter();

  // সব hook এখানে — conditional return এর আগে
  useEffect(() => {
    const fetchStoresForSwitch = async () => {
      try {
        const { data } = await AxiosInstance.get("/api/merchant_user/seller-status/");
        if (data.possible_stores) {
          setStores(data.possible_stores.filter((s) => s.status === "approved"));
        }
      } catch (err) {
        console.warn("Cannot load stores for switch", err);
      }
    };

    if (isAuthenticated) {
      fetchStoresForSwitch();
    }
  }, [isAuthenticated]);

  const handleSwitchStore = (store) => {
    localStorage.setItem(
      "ORGANIZATION_DOMAIN",
      store.store_url.replace(/^https?:\/\//, "")
    );
    localStorage.setItem("ACTIVE_ORG_ID", store.org_id);
    localStorage.setItem("ACTIVE_BUSINESS_EMAIL", store.business_email);

    toast.success(`Switched to: ${store.business_name}`);
    setOpen(false);

    window.location.href = "/store"; // বা router.replace("/store")
  };

  const handleLogout = () => {
    localStorage.removeItem("Token");
    localStorage.removeItem("RefreshToken");
    router.push("/auth/login");
  };

  // এখন loading চেক — সব hook শেষ হওয়ার পর
  if (loading) {
    return (
      <div className="flex items-center justify-between px-12 py-3 border-b">
        <span>Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between px-12 py-3 border-b border-slate-200 bg-white">
      {/* LOGO */}
      <Link href="/" className="relative text-4xl font-semibold text-slate-700">
        <span className="text-green-600">go</span>cart
        <span className="text-green-600 text-5xl">.</span>
        <p className="absolute text-xs font-semibold -top-1 -right-11 px-3 py-0.5 rounded-full text-white bg-green-500">
          Store
        </p>
      </Link>

      {/* USER MENU */}
      <div className="relative">
        {isAuthenticated ? (
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-slate-700 hover:bg-slate-100"
          >
            <span>
              Hi, <strong>{user?.first_name}</strong>
            </span>
            <ChevronDown size={16} />
          </button>
        ) : (
          <Link href="/auth/login" className="text-slate-600 hover:underline">
            Login
          </Link>
        )}

        {/* DROPDOWN */}
        {open && (
          <div className="absolute right-0 mt-2 w-56 bg-white border rounded-lg shadow-xl z-50 divide-y divide-slate-100">

            {/* Switch Store Section */}
            {stores.length > 1 && (
              <div className="py-2">
                <p className="px-4 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  Switch Store
                </p>
                {stores.map((store) => (
                  <button
                    key={store.org_id}
                    onClick={() => handleSwitchStore(store)}
                    className={`w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 flex items-center gap-3 ${
                      localStorage.getItem("ACTIVE_ORG_ID") === store.org_id
                        ? "bg-blue-50 font-medium"
                        : ""
                    }`}
                  >
                    {store.store_logo ? (
                      <img
                        src={store.store_logo}
                        alt={store.business_name}
                        className="w-8 h-8 rounded-full object-cover border"
                      />
                    ) : (
                      <Building2 size={20} className="text-slate-400" />
                    )}
                    <span className="truncate">{store.business_name}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Profile & Dashboard */}
            <div className="py-1">
              <Link
                href="/store/profile"
                className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                <User size={16} />
                Profile
              </Link>

              <Link
                href="/store/dashboard"
                className="block px-4 py-2.5 text-sm hover:bg-slate-50"
                onClick={() => setOpen(false)}
              >
                Store Dashboard
              </Link>
            </div>

            {/* Logout */}
            <div className="py-1">
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StoreNavbar;