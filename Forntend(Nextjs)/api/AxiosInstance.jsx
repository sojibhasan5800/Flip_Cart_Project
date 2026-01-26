// api/AxiosInstance.jsx
import axios from "axios";
const PUBLIC_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

const AxiosInstance = axios.create({
  baseURL: PUBLIC_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Request interceptor
AxiosInstance.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("Token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    if (config.useTenant === true) {
      const tenantDomain = localStorage.getItem("ORGANIZATION_DOMAIN");
      if (tenantDomain) {
        // লোকালহোস্টে http, প্রোডাকশনে https
        const isLocalhost = tenantDomain.includes("127.0.0.1") || tenantDomain.includes("localhost");
        config.baseURL = isLocalhost
          ? `http://${tenantDomain}`    // লোকালহোস্টে http
          : `https://${tenantDomain}`   // প্রোডাকশনে https
          console.log("Tenant domain:", tenantDomain);
      }
    } else {
      config.baseURL = PUBLIC_BASE_URL;
    }
    return config;
  },
  (error) => Promise.reject(error)
);


// Response interceptor ( main logic)
AxiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 + retry না করা হলে
    if (
      error.response?.status === 401 &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("RefreshToken");

        if (!refreshToken) {
          throw new Error("No refresh token");
        }

        // 🔁 refresh token API call
        const res = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}api/accounts/token/refresh/`,
          {
            refresh: refreshToken,
          }
        );

         // 🔴 CHANGE-2: access token save
        const newAccessToken = res.data.access;

        // 🔐 localStorage update
        localStorage.setItem("Token", newAccessToken);

        // 🔴 CHANGE-3: refresh token save (VERY IMPORTANT)
        if (res.data.refresh) {
          localStorage.setItem("RefreshToken", res.data.refresh);
        }

        // 🔁 header update
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        // 🔁 আগের request আবার পাঠানো
        return AxiosInstance(originalRequest);
      } catch (refreshError) {
        // refresh token fail হলে logout
        localStorage.removeItem("Token");
        localStorage.removeItem("RefreshToken");
        window.location.href = "/auth/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default AxiosInstance;
