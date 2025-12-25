// api/AxiosInstance.jsx
import axios from "axios";

const AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
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
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (🔥 main logic)
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
          `${process.env.NEXT_PUBLIC_API_URL}/api/accounts/token/refresh/`,
          {
            refresh: refreshToken,
          }
        );

        const newAccessToken = res.data.access;

        // 🔐 localStorage update
        localStorage.setItem("Token", newAccessToken);

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
