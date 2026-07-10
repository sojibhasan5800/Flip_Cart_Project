"use client"

import {  User, Package, LogOut, PackageIcon, Search, ShoppingCart,CreditCard,MapPin } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
// import { Crown, Sparkles } from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
// import { logout as logoutAction } from "../../../../store/authSlice";


const Navbar = () => {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const cartCount = useSelector((state) => state.cart.total);
  const dispatch = useDispatch();
  const [isPlusMember, setIsPlusMember] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  // const isLoggedIn = useSelector((state) => state.auth.isLoggedIn);

  // Check token in localStorage to see if user is logged in


  useEffect(() => {
    const token = localStorage.getItem("Token");
    setIsLoggedIn(!!token);
    const checkMembership = async () => {
    const storedStatus = localStorage.getItem("isPlusMember");

    if (storedStatus !== null) {
      //  Use cached value
      setIsPlusMember(storedStatus === "true");
      return;
    }

    try {


      const res = await fetch("/api/check-membership");

      const data = await res.json();

      // assume API returns: { isPlus: true/false }
      localStorage.setItem("isPlusMember", data.isPlus);
      setIsPlusMember(data.isPlus);

    } catch (error) {
      console.error("Membership check failed", error);
      setIsPlusMember(false);
    }
  };

  checkMembership();
}, []);

  const handleLogout = () => {
    localStorage.removeItem("Token");
    setIsLoggedIn(false);
    router.push("/auth/login");
  };

  // const handleLogout = () => {
  //   localStorage.removeItem("Token");
  //   localStorage.removeItem("RefreshToken");
  //   dispatch(logoutAction());
  //   router.push("/auth/login");
  // };

  const [search, setSearch] = useState("");
  const handleSearch = (e) => {
    e.preventDefault();
    router.push(`/shop?search=${search}`);
  };

  return (
    <nav className="relative bg-white">
      <div className="mx-6">
        <div className="flex items-center justify-between max-w-7xl mx-auto py-4 transition-all">
          <Link href="/" className="relative text-4xl font-semibold text-slate-700">
            <span className="text-green-600">go</span>cart
            <span className="text-green-600 text-5xl leading-0">.</span>
            {/* <p className="absolute text-xs font-semibold -top-1 -right-8 px-3 p-0.5 rounded-full flex items-center gap-2 text-white bg-green-500">
              plus
            </p> */}

            {isPlusMember !== null && (
              <p className={`absolute text-xs font-semibold -top-1 -right-8 px-3 p-0.5 rounded-full flex items-center gap-2 text-white 
                ${isPlusMember ? "bg-green-500" : "bg-gray-400"}`}>
                
                {isPlusMember ? "plus" : "basic"}
              </p>
            )}
          </Link>

          {/* Desktop Menu */}
          <div className="hidden sm:flex items-center gap-4 lg:gap-8 text-slate-600">
            <Link href="/">Home</Link>
            <Link href="/shop">Shop</Link>
            <Link href="/">About</Link>
            <Link href="/">Contact</Link>

            <form onSubmit={handleSearch} className="hidden xl:flex items-center w-xs text-sm gap-2 bg-slate-100 px-4 py-3 rounded-full">
              <Search size={18} className="text-slate-600" />
              <input
                className="w-full bg-transparent outline-none placeholder-slate-600"
                type="text"
                placeholder="Search products"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                required
              />
            </form>

            <Link href="/cart" className="relative flex items-center gap-2 text-slate-600">
              <ShoppingCart size={18} /> Cart
              <span className="absolute -top-1 left-3 text-[8px] text-white bg-slate-600 rounded-full">
                {cartCount}
              </span>
            </Link>

            {/* Login / Logout Button */}
        {isLoggedIn ? (
<div className="relative">
  <button
    onClick={() => setShowProfileMenu(!showProfileMenu)}
    className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold"
  >
    S
  </button>

  {showProfileMenu && (
    <div className="absolute right-0 mt-3 w-72 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-50">

      {/* User Info */}
      <div className="p-4 border-b">
        <h3 className="font-semibold text-slate-800">
          Sojib Ahmed
        </h3>
        <p className="text-sm text-slate-500">
          sojib@gmail.com
        </p>
      </div>

      {/* Menu */}
      <div className="py-2">

        <Link
          href="/account"
          className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
        >
          <User size={18} />
          <span>Manage Account</span>
        </Link>

        <Link
          href="/billing/customer_billing/"
          className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
        >
          <CreditCard size={18} />
          <span>Billing & Payments</span>
        </Link>

        <Link
          href="/orders"
          className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
        >
          <Package size={18} />
          <span>My Orders</span>
        </Link>

        <Link
          href="/cart"
          className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
        >
          <ShoppingCart size={18} />
          <span>Cart</span>
        </Link>

        <Link
          href="/addresses"
          className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"
        >
          <MapPin size={18} />
          <span>Addresses</span>
        </Link>

      </div>

      {/* Logout */}
      <div className="border-t">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 text-red-500 hover:bg-red-50"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>

    </div>
  )}
</div>
): (
              <Link href="/auth/login">
                <button className="px-8 py-2 bg-indigo-500 hover:bg-indigo-600 transition text-white rounded-full">
                  Login
                </button>               
              </Link>
            )}
          </div>

          {/* Mobile Menu */}
          <div className="sm:hidden">
            {isLoggedIn ? (
              <div className="flex gap-2">
                <Link href="/cart">
                  <button className="px-4 py-1.5 bg-gray-500 text-white rounded-full text-sm">Cart</button>
                </Link>
                <Link href="/orders">
                  <button className="px-4 py-1.5 bg-gray-500 text-white rounded-full text-sm">My Orders</button>
                </Link>
                <button
                  onClick={handleLogout}
                  className="px-4 py-1.5 bg-red-500 text-white rounded-full text-sm"
                >
                  Logout
                </button>
              </div>
            ) : (
              <Link href="/auth/login">
                <button className="px-7 py-1.5 bg-indigo-500 hover:bg-indigo-600 text-sm text-white rounded-full">
                  Login
                </button>
              </Link>
            )}
          </div>
        </div>
      </div>
      <hr className="border-gray-300" />
    </nav>
  );
};

export default Navbar;
