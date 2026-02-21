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

            setSettings(prev => ({
              ...prev,
              enabled: msg.data.enabled,
              interval_minutes: msg.data.interval_minutes,
              resume_at: msg.data.resume_at
            }))

            toast.info("Dashboard settings updated by admin", { duration: 2000 })

            if (msg.data.resume_at) {
              const resumeTime = new Date(msg.data.resume_at)
              const now = new Date()
              const diffSeconds = Math.floor((resumeTime - now) / 1000)
              setCountdown(diffSeconds > 0 ? diffSeconds : 0)
            } else {
              setCountdown(null)
            }

          // setSettings(msg.data)
          // toast.info("Dashboard settings updated by admin", { duration: 2000 })
          // // Resume_at থেকে countdown calculate
          // if (msg.data.resume_at) {
          //   const resumeTime = new Date(msg.data.resume_at)
          //   const now = new Date()
          //   const diffSeconds = Math.floor((resumeTime - now) / 1000)
          //   setCountdown(diffSeconds > 0 ? diffSeconds : 0)
          // } else {
          //   setCountdown(null)
          // }
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

    if (!settings.enabled) return

    // 🆕 Always reset when interval changes
    setCountdown(settings.interval_minutes * 60)

    const intervalId = setInterval(() => {
      setCountdown(prev => {

        if (prev <= 1) {
          return settings.interval_minutes * 60
        }

        return prev - 1
      })
    }, 1000)

    return () => clearInterval(intervalId)

  }, [settings.enabled, settings.interval_minutes])

return (
  <div className="mb-6">
    {settings.enabled ? (
      <div className="bg-white shadow-md rounded-xl p-5 border border-green-200">

        {/* Header */}
        <div className="flex justify-between items-center mb-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Dashboard Scheduler
            </h2>
            <p className="text-sm text-gray-500">
              Automatic live update configuration
            </p>
          </div>

          <span className="bg-green-100 text-green-700 text-xs font-medium px-3 py-1 rounded-full">
            ● Active
          </span>
        </div>

        {/* Interval Info */}
        <div className="flex items-center justify-between bg-green-50 p-4 rounded-lg">

          <div>
            <p className="text-sm text-gray-600">Update Interval</p>
            <h3 className="text-xl font-bold text-green-700">
              {settings.interval_minutes} Minute
              {settings.interval_minutes > 1 && "s"}
            </h3>
          </div>

          {/* Countdown */}
          <div className="text-right">
            <p className="text-sm text-gray-600">Next Update In</p>
            <div className="text-2xl font-mono font-bold text-blue-600">
              {Math.floor(countdown / 60)}:
              {(countdown % 60).toString().padStart(2, '0')}
            </div>
          </div>

        </div>
      </div>
    ) : (
      <div className="bg-white shadow-md rounded-xl p-5 border border-yellow-300">

        {/* Header */}
        <div className="flex justify-between items-center mb-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              Dashboard Scheduler
            </h2>
            <p className="text-sm text-gray-500">
              Automatic live update configuration
            </p>
          </div>

          <span className="bg-yellow-100 text-yellow-700 text-xs font-medium px-3 py-1 rounded-full">
            ● Paused
          </span>
        </div>

        {/* Pause Info */}
        <div className="bg-yellow-50 p-4 rounded-lg">

          <p className="text-yellow-800 font-medium mb-2">
            Automatic updates are temporarily disabled by admin.
          </p>

          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Resuming In
            </p>

            <div className="text-xl font-mono font-bold text-red-600">
              {Math.floor(countdown / 60)} min{" "}
              {(countdown % 60).toString().padStart(2, '0')} sec
            </div>
          </div>

        </div>
      </div>
    )}
  </div>
)

}