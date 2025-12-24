// utils/axios.js
import axios from "axios";

const AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL, // আপনার backend URL
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  withCredentials: false, // JWT workflow এ cookie দরকার নেই
});

// Request interceptor: automatically attach token if exists
AxiosInstance.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("Token");
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 Unauthorized
AxiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // token expired বা invalid হলে localStorage clear
      if (typeof window !== "undefined") {
        localStorage.removeItem("Token");
        localStorage.removeItem("RefreshToken");
      }
      window.location.href = "/auth/login"; // redirect to login page
    }
    return Promise.reject(error);
  }
);

export default AxiosInstance;
