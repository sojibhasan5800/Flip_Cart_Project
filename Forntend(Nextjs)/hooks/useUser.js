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
        const res = await AxiosInstance.get("/api/accounts/dashboard/");
        setUser(res.data.user); // 👈 এখানে user object
      } catch (err) {
        console.error("User fetch failed:", err);
        setError(err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [isAuthenticated]);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin: user?.is_admin || false,
    isSuperAdmin: user?.is_superadmin || false,
    isTenantOwner: user?.is_tenant_owner || false,
  };
};

export default useUser;
