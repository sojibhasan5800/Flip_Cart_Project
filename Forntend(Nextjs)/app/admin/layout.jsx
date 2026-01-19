"use client";
import AdminLayout from "@/components/admin/AdminLayout";
import AxiosInstance from "../../api/AxiosInstance"
import { useEffect, useState } from "react";
import useToken from "../../hooks/useToken";
import useAuth from "../../hooks/useAuth";


// export const metadata = {
//     title: "GoCart. - Admin",
//     description: "GoCart. - Admin",
// };
const checkPublicAdmin = async (token) => {
    const res = await AxiosInstance.get("/api/admin_core/check/",{
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    console.log("response", res.data);
    return res.data;
  };

  export default function RootAdminLayout({ children }) {
    const {token} = useToken();
    const {isAuthenticated} = useAuth();
    console.log("token", token);
    console.log("user", isAuthenticated);
    const [allowed, setAllowed] = useState(null);
  
    useEffect(() => {
      checkPublicAdmin(token)
        .then((res) => {
          setAllowed(res.is_public_admin);
        })
        .catch((error) => {
          console.error("Admin check failed:", error);
          setAllowed(false);
        });
    }, [token]);
  
    //  Loading state
    if (allowed === null) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <p className="text-gray-600">Checking admin permission...</p>
        </div>
      );
    }
  
    //  Not public admin → custom design
    if (!allowed) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
          <div className="bg-white p-6 rounded shadow-md max-w-md text-center">
            <h2 className="text-xl font-bold text-red-500 mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600">
              You are not allowed to access the Public Admin Panel.
            </p>
          </div>
        </div>
      );
    }
  
    //  Public schema super admin → real admin layout
    return <AdminLayout>{children}</AdminLayout>;
  }
  