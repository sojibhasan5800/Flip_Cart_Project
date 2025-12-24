"use client";

import { useState } from "react";
import { Box, TextField, Button, Typography, Alert } from "@mui/material";
import Link from "next/link";
import AxiosInstance from "../../../../../api/AxiosInstance";

export default function ForgetPasswordPage() {
  const [email, setEmail] = useState("");
  const [showMessage, setShowMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setShowMessage("");
    setLoading(true);

    try {
      await AxiosInstance.post("password_reset/", { email });
      setShowMessage("Password reset email sent! Check your inbox.");
    } catch (error) {
      console.error("Password reset error:", error);
      setShowMessage(
        error.response?.data?.detail || "Failed to send reset email."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "84vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 2,
        background: "#f8f9fa", // same background as login/register
      }}
    >
      {/* Card Container */}
      <Box
        sx={{
          backgroundColor: "#fff",
          maxWidth: 400,
          width: "100%",
          borderRadius: 3,
          boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
          p: { xs: 2, sm: 3, md: 4 },
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h5"
          component="h4"
          sx={{ mb: 2, fontWeight: "bold", textAlign: "center" }}
        >
          Forgot Password
        </Typography>

        {showMessage && (
          <Alert
            severity={showMessage.includes("Failed") ? "error" : "success"}
            sx={{ mb: 2, width: "100%" }}
          >
            {showMessage}
          </Alert>
        )}

        {/* Form */}
        <Box component="form" onSubmit={handleSubmit} sx={{ width: "100%" }}>
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

          <Box sx={{ mb: 1.5, textAlign: "right" }}>
            <Link
              href="/auth/login"
              style={{ color: "#1976d2", textDecoration: "none", fontSize: 14 }}
            >
              Got password? Login
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
            {loading ? "Submitting..." : "Submit"}
          </Button>
        </Box>
      </Box>

      {/* Sign Up link */}
      <Typography sx={{ mt: 2, textAlign: "center" }}>
        Don't have an account?{" "}
        <Link
          href="/auth/register"
          style={{ color: "#1976d2", textDecoration: "none" }}
        >
          Sign up
        </Link>
      </Typography>
    </Box>
  );
}
