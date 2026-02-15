'use client'
import { useEffect } from 'react'
import toast from 'react-hot-toast'

export default function DashboardLive({ orgId, onUpdate }) {
  useEffect(() => {
    if (!orgId) {
      console.warn("No orgId found for WebSocket")
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsHost = window.location.host
    const wsUrl = `${protocol}://localhost:8001/ws/dashboard/${orgId}/`

    console.log("Connecting to WebSocket:", wsUrl)

    const socket = new WebSocket(wsUrl)
    let pingInterval

    socket.onopen = () => {
      console.log("WebSocket connected")

      // ✅ toast একবার দেখাবে
      toast.success("Live updates enabled", { duration: 3000 })

      // ৩০ সেকেন্ডে ping পাঠাবে
      pingInterval = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }))
        }
      }, 30000)
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'dashboard_update' && msg.data) {
          onUpdate(msg.data)
        }
      } catch (err) {
        console.error("WebSocket message parse error:", err)
      }
    }

    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
      toast.error("Live update connection failed")
    }

    socket.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason)
      // normal closure নয়, reconnect
      if (event.code !== 1000) {
        setTimeout(() => {
          console.log("Attempting to reconnect WebSocket...")
          // optional: নতুন WebSocket তৈরি করতে পারো
        }, 5000)
      }
    }

    // Cleanup
    return () => {
      console.log("Cleaning up WebSocket")
      if (pingInterval) clearInterval(pingInterval)
      socket.close(1000, "Component unmounted")
    }
  }, [orgId]) // ✅ onUpdate dependency সরানো
  return null
}
