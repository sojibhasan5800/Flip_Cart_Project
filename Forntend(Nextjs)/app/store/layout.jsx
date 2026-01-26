"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import StoreLayout from "@/components/store/StoreLayout";
import useUser from "../../hooks/useUser";

export default function StoreRootLayout({ children }) {
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/auth/login");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Checking authentication...</p>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return <StoreLayout>{children}</StoreLayout>;
}
