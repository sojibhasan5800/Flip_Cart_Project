"use client";

import { useEffect, useState } from "react";
import AxiosInstance from "../api/AxiosInstance";
import useAuth from "./useAuth";

const useUser = () => {
  const { isAuthenticated } = useAuth();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setUser(null);
      setLoading(false);
      return;
    }

    const fetchUser = async () => {
      try {
        setLoading(true);
        const res = await AxiosInstance.get("/api/accounts/user-detail/");
        setUser(res.data?.data || null);
        setError(null);
      } catch (err) {
        console.error("User fetch failed:", err);
        setUser(null);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [isAuthenticated]);

  return {
    user,
    isAuthenticated,
    loading,
    error,
    //  ROLE MAPPING (THIS IS THE KEY)
    isAdmin: user?.roles?.is_admin || user?.roles?.is_superadmin || false,
    isSuperAdmin: user?.roles?.is_superadmin || false,
    isTenantOwner: user?.roles?.is_tenant_owner || false,
    isTenantStaff: user?.roles?.is_tenant_staff || false,
  };
};

export default useUser;
