"use client";

import { useState } from "react";
import { Box, TextField, Button, Typography, Alert } from "@mui/material";
import AxiosInstance from "../../../../api/AxiosInstance";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useDispatch } from "react-redux";
// import { login as loginAction } from "../../../../store/authSlice";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams(); // For query params like ?command=verification
  const emailVerified = searchParams.get("command") === "verification";
  const verifiedEmail = searchParams.get("email");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showError, setShowError] = useState(false);
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch();
  



  const handleLogin = async (e) => {
    e.preventDefault();
    setShowError(false);
    setLoading(true);

    try {
      const response = await AxiosInstance.post("api/accounts/login/", { email, password });

        // Save JWT tokens
    localStorage.setItem("Token", response.data.access);
    localStorage.setItem("RefreshToken", response.data.refresh);
    // Update Redux state
    // dispatch(loginAction());
    router.push("/"); // redirect after login

    } catch (err) {
      console.error("Login error:", err);
      setShowError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "84vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 2,
        background: "#f8f9fa",
      }}
    >
      {emailVerified ? (
        <Box
          sx={{
            maxWidth: 500,
            textAlign: "center",
            bgcolor: "info.main",
            color: "white",
            p: 3,
            borderRadius: 2,
            boxShadow: 2,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Thank you for registering with us. We have sent you a verification email to{" "}
            <strong>{verifiedEmail}</strong>.
          </Typography>
          <Typography variant="body1" sx={{ mt: 2 }}>
            Already verified?{" "}
            <Link href="/auth/login" style={{ color: "#fff", textDecoration: "underline" }}>
              Login
            </Link>
          </Typography>
        </Box>
      ) : (
        <Box
          component="form"
          onSubmit={handleLogin}
          sx={{
            backgroundColor: "#fff",
            padding: { xs: 2, sm: 3, md: 4 },
            borderRadius: 3,
            boxShadow: "0 4px 30px rgba(0,0,0,0.2)",
            width: {
              xs: "90%",
              sm: "70%",
              md: "50%",
              lg: "40%",
            },
            maxWidth: 400,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Typography
            variant="h5"
            component="h1"
            gutterBottom
            sx={{ fontWeight: "bold", textAlign: "center", mb: 2 }}
          >
            Sign in
          </Typography>

          {showError && (
            <Alert severity="error" sx={{ mb: 2, width: "100%" }}>
              Login failed! Please check your credentials.
            </Alert>
          )}

          <TextField
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            size="small"
            required
            sx={{ mb: 1.5 }}
          />

          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            size="small"
            required
            sx={{ mb: 1.5 }}
          />

          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1.5, width: "100%" }}>
            <Link
              href="/auth/temp_password/password_reset"
              style={{ color: "#1976d2", textDecoration: "none", fontSize: 14 }}
            >
              Forgot password?
            </Link>
          </Box>

          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ py: 1.3, mb: 1.5 }}
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </Button>

          <Typography variant="body2" sx={{ textAlign: "center" }}>
            Don't have an account?{" "}
            <Link href="/auth/register" style={{ color: "#1976d2", textDecoration: "none" }}>
              Sign up
            </Link>
          </Typography>
        </Box>
      )}
    </Box>
  );
}
