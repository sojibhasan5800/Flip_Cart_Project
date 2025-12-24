"use client";
import { useSearchParams } from "next/navigation";
import { Box, Typography, Alert, Button } from "@mui/material";
import Link from "next/link";

export default function RegisterActivePage() {
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "your email";
  const fullName = searchParams.get("fullName") || "your name";

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
        sx={{
          backgroundColor: "#fff",
          padding: { xs: 3, sm: 4, md: 5 },
          borderRadius: 3,
          boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
          width: { xs: "90%", sm: "70%", md: "50%", lg: "40%" },
          maxWidth: 500,
          textAlign: "center",
        }}
      >
        <Typography
          variant="h5"
          component="h1"
          gutterBottom
          sx={{ fontWeight: "bold", mb: 2, color: "#1976d2" }}
        >
          Registration Successful!
        </Typography>
        <Alert severity="success" sx={{ mb: 3, justifyContent: "center" }}>
          Activation link has been sent to your email <strong>{email}</strong> for <strong>{fullName}</strong>.
        </Alert>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Please check your inbox (and spam folder) to activate your account.
        </Typography>
        <Link href="/auth/login" passHref>
          <Button variant="contained" color="primary" fullWidth sx={{ py: 1.5 }}>
            Go to Login
          </Button>
        </Link>
      </Box>
    </Box>
  );
}