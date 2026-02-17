'use client'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

export default function DashboardLive({ orgId, onUpdate }) {
  const [socket, setSocket] = useState(null)
  const [settings, setSettings] = useState({ enabled: true, interval_minutes: 1, resume_at: null })
  const [countdown, setCountdown] = useState(null)

  useEffect(() => {
    if (!orgId) {
      console.warn("No orgId found for WebSocket")
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsHost = process.env.NEXT_PUBLIC_WS_HOST_URL 
    const wsUrl = `${protocol}://${wsHost}/ws/dashboard/${orgId}/`

    console.log("Connecting to WebSocket:", wsUrl)

    const ws = new WebSocket(wsUrl)
    setSocket(ws)

    let pingInterval

    ws.onopen = () => {
      console.log("WebSocket connected")
      toast.success("Live updates enabled", { duration: 3000 })
      pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }))
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'dashboard_update' && msg.data) {
          onUpdate(msg.data)
        }
        if (msg.type === 'scheduler_settings' && msg.data) {
          setSettings(msg.data)
          toast.info("Dashboard settings updated by admin", { duration: 2000 })
          // Resume_at থেকে countdown calculate
          if (msg.data.resume_at) {
            const resumeTime = new Date(msg.data.resume_at)
            const now = new Date()
            const diffSeconds = Math.floor((resumeTime - now) / 1000)
            setCountdown(diffSeconds > 0 ? diffSeconds : 0)
          } else {
            setCountdown(null)
          }
        }
      } catch (err) {
        console.error("WebSocket message parse error:", err)
      }
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      toast.error("Live update connection failed")
    }

    ws.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason)
      if (event.code !== 1000) {
        setTimeout(() => {
          console.log("Attempting to reconnect WebSocket...")
        }, 5000)
      }
    }

    // Cleanup
    return () => {
      console.log("Cleaning up WebSocket")
      if (pingInterval) clearInterval(pingInterval)
      ws.close(1000, "Component unmounted")
    }
  }, [orgId, onUpdate])

  // Countdown timer logic
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000)
      return () => clearTimeout(timer)
    } else if (countdown === 0) {
      setSettings(prev => ({ ...prev, enabled: true, resume_at: null }))
      toast.success("Automatic updates resumed!")
    }
  }, [countdown])

  // Next update countdown যদি enabled থাকে
  useEffect(() => {
    if (settings.enabled && countdown === null) {
      setCountdown(settings.interval_minutes * 60)  // initial to next update
      const interval = setInterval(() => {
        setCountdown(c => (c > 0 ? c - 1 : settings.interval_minutes * 60))
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [settings.enabled, settings.interval_minutes])

  return (
    <div className="mb-4">
      {settings.enabled ? (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <span>✅ Live updates every {settings.interval_minutes} min</span>
          <button className="bg-blue-100 px-2 py-1 rounded" title="Next update time">
            Next in: {Math.floor(countdown / 60)}:{(countdown % 60).toString().padStart(2, '0')}
          </button>
        </div>
      ) : (
        <div className="bg-yellow-100 border border-yellow-300 rounded p-3 text-sm">
          <p className="font-medium text-yellow-800">Automatic updates paused by admin</p>
          <p>Resuming in: {Math.floor(countdown / 60)} min {(countdown % 60).toString().padStart(2, '0')} sec</p>
        </div>
      )}
    </div>
  )
}