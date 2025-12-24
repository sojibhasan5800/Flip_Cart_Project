"use client";

import { useState } from "react";
import { Box, TextField, Button, Typography, Alert, Grid } from "@mui/material";
import AxiosInstance from "../../../../api/AxiosInstance";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone_number: "",
    password: "",
    confirm_password: "",
  });

  const [showError, setShowError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // const handleRegister = async (e) => {
  //   e.preventDefault();
  //   setShowError("");

  //   if (formData.password !== formData.confirm_password) {
  //     setShowError("Passwords do not match");
  //     return;
  //   }

  //   setLoading(true);
  //   try {
  //     await AxiosInstance.post("api/accounts/register/", {
  //       first_name: formData.first_name,
  //       last_name: formData.last_name,
  //       email: formData.email,
  //       phone_number: formData.phone_number,
  //       password: formData.password,
  //       confirm_password: formData.confirm_password,
  //     });
  //     const fullName = `${formData.first_name} ${formData.last_name}`;
  //     router.push(`/auth/register_active?email=${encodeURIComponent(formData.email)}&fullName=${encodeURIComponent(fullName)}`);
  //   } catch (err) {
  //     setShowError(
  //       err.response?.data?.detail ||
  //         "Registration failed. Please try again."
  //     );
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const handleRegister = async (e) => {
  e.preventDefault();
  setShowError("");
  if (formData.password !== formData.confirm_password) {
    setShowError("Passwords do not match");
    return;
  }
  setLoading(true);
  try {
    const response = await AxiosInstance.post("api/accounts/register/", {
      first_name: formData.first_name,
      last_name: formData.last_name,
      email: formData.email,
      phone_number: formData.phone_number,
      password: formData.password,
      confirm_password: formData.confirm_password,
    });
    // সাকসেস: details নিয়ে রিডিরেক্ট (query params দিয়ে)
    const fullName = `${response.data.first_name} ${response.data.last_name}`;
    router.push(`/auth/register_active?email=${encodeURIComponent(response.data.email)}&name=${encodeURIComponent(fullName)}`);
  } catch (err) {
    let errorMessage = "Registration failed. Please try again.";
    if (err.response) {
      const status = err.response.status;
      if (status === 400) {
        errorMessage = "Invalid data provided. Check your inputs (e.g., email already exists).";
      } else if (status === 500) {
        errorMessage = "Server error. Please try later.";
      } else {
        errorMessage = err.response?.data?.detail || errorMessage;
      }
    }
    setShowError(errorMessage);
  } finally {
    setLoading(false);
  }
};
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(to right, #6a11cb, #2575fc)",
        padding: 2,
      }}
    >
      <Box
        component="form"
        onSubmit={handleRegister}
        sx={{
          backgroundColor: "#fff",
          padding: { xs: 2, sm: 3, md: 4 },
          borderRadius: 3,
          boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
          width: {
            xs: "90%",  // Mobile
            sm: "70%",  // Tablet
            md: "50%",  // Laptop
            lg: "40%",  // Large Screen
          },
          maxWidth: 400, // Medium size
          display: "flex",
          flexDirection: "column",
          alignItems: "center", // All fields centered
        }}
      >
        <Typography
          variant="h4"
          component="h1"
          gutterBottom
          sx={{ fontWeight: "bold", textAlign: "center", mb: 2 }}
        >
          Sign Up
        </Typography>

        {showError && (
          <Alert severity="error" sx={{ mb: 2, width: "100%" }}>
            {showError}
          </Alert>
        )}

        <Grid container spacing={1} sx={{ width: "100%" }}>
          <Grid item xs={12} md={6}>
            <TextField
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              fullWidth
              size="small" // Compact size
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              fullWidth
              size="small"
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Email Address"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              fullWidth
              size="small"
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Phone Number"
              name="phone_number"
              value={formData.phone_number}
              onChange={handleChange}
              fullWidth
              size="small"
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              fullWidth
              size="small"
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Confirm Password"
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              fullWidth
              size="small"
              required
            />
          </Grid>
        </Grid>

        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2, py: 1.3 }}
          disabled={loading}
        >
          {loading ? "Registering..." : "Register"}
        </Button>

        <Box sx={{ mt: 1.5, textAlign: "center" }}>
          <Typography variant="body2">
            Already have an account?{" "}
            <Link
              href="/auth/login"
              style={{ color: "#1976d2", textDecoration: "none" }}
            >
              Login here
            </Link>
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
