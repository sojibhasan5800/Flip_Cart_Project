'use client'
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import AxiosInstance from '@/api/AxiosInstance'

export default function DashboardSchedulerToggle() {
  const [enabled, setEnabled] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchStatus = async () => {
    try {
      const { data } = await AxiosInstance.get('/api/admin_core/dashboard-scheduler/control/')
      setEnabled(data.enabled)
    } catch (err) {
      toast.error('Failed to fetch scheduler status')
    } finally {
      setLoading(false)
    }
  }

  const toggleScheduler = async () => {
    const action = enabled ? 'disable' : 'enable'
    try {
      setLoading(true)
      const { data } = await AxiosInstance.post('/api/admin_core/dashboard-scheduler/control/', { action })
      setEnabled(data.enabled)
      toast.success(`Scheduler ${action}d`)
    } catch (err) {
      toast.error('Failed to update scheduler')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  if (loading) return <div className="text-gray-500">Loading scheduler status...</div>

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg border shadow-sm">
      <div>
        <h3 className="font-medium">Real-time Dashboard Updates</h3>
        <p className="text-sm text-gray-600">
          {enabled 
            ? 'Active: Updates every 1 minute for online merchants' 
            : 'Paused: No automatic updates'}
        </p>
      </div>

      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={enabled}
          onChange={toggleScheduler}
          className="sr-only peer"
          disabled={loading}
        />
        <div className={`w-14 h-7 bg-gray-200 rounded-full peer 
          peer-checked:after:translate-x-7 after:content-[''] after:absolute 
          after:top-0.5 after:left-0.5 after:bg-white after:rounded-full 
          after:h-6 after:w-6 after:transition-all
          ${enabled ? 'peer-checked:bg-green-600' : ''}`}>
        </div>
      </label>
    </div>
  )
}