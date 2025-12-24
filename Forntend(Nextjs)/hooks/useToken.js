import { useState, useEffect } from "react";

const useToken = () => {
  const [token, setToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);

  useEffect(() => {
    if (typeof window === "undefined") return; // SSR এ skip

    const storedToken = localStorage.getItem("Token");
    const storedRefreshToken = localStorage.getItem("RefreshToken");

    setToken(storedToken);
    setRefreshToken(storedRefreshToken);

    const updateTokens = () => {
      setToken(localStorage.getItem("Token") || null);
      setRefreshToken(localStorage.getItem("RefreshToken") || null);
    };

    window.addEventListener("storage", updateTokens);

    return () => {
      window.removeEventListener("storage", updateTokens);
    };
  }, []);

  return { token, refreshToken };
};

export default useToken;
