"use client";

import { useState } from "react";
import { Box, Button, Typography, Modal } from "@mui/material";
import AxiosInstance from "../api/AxiosInstance";
import { useRouter } from "next/navigation";

export default function LogoutModal({ open, handleClose }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleLogout = async () => {
    setLoading(true);
    try {
      await AxiosInstance.post("api/accounts/logout/"); // Backend logout API
      localStorage.removeItem("Token");
      localStorage.removeItem("RefreshToken");
      router.push("/auth/login"); // redirect to login page
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      setLoading(false);
      handleClose(); // close modal
    }
  };

  return (
    <Modal open={open} onClose={handleClose} aria-labelledby="logout-modal-title">
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: { xs: 300, sm: 350 },
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 24,
          p: 4,
          textAlign: "center",
        }}
      >
        <Typography id="logout-modal-title" variant="h6" sx={{ mb: 2, fontWeight: "bold" }}>
          Are you sure you want to logout?
        </Typography>
        <Box sx={{ display: "flex", justifyContent: "space-between", mt: 3 }}>
          <Button
            variant="outlined"
            color="inherit"
            onClick={handleClose}
            sx={{ width: "45%" }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleLogout}
            sx={{ width: "45%" }}
            disabled={loading}
          >
            {loading ? "Logging out..." : "Logout"}
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}
