'use client'
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import AxiosInstance from '@/api/AxiosInstance'

export default function DashboardSchedulerControl() {
  const [settings, setSettings] = useState({
    enabled: true,
    intervalMinutes: 1,
    resumeInMinutes: null,
  })
  const [loading, setLoading] = useState(true)
  const [offDuration, setOffDuration] = useState(30) // default 30 min
  const [newInterval, setNewInterval] = useState(1)

  const fetchSettings = async () => {
    try {
      const { data } = await AxiosInstance.get('/api/system_management/dashboard-scheduler/control/')
      setSettings({
        enabled: data.enabled,
        intervalMinutes: data.interval_minutes,
        resumeInMinutes: data.resume_in_minutes,
      })
    } catch (err) {
      toast.error('Failed to load scheduler settings')
    } finally {
      setLoading(false)
    }
  }

  const updateSettings = async (payload) => {
    try {
      setLoading(true)
      const { data } = await AxiosInstance.post('/api/system_management/dashboard-scheduler/control/', payload)
      setSettings({
        enabled: data.enabled,
        intervalMinutes: data.interval_minutes,
        resumeInMinutes: data.resume_in_minutes || null,
      })
      toast.success('Settings updated')
    } catch (err) {
      toast.error('Update failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSettings()
    const interval = setInterval(fetchSettings, 30000) // every 30s refresh
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div>Loading scheduler...</div>

  return (
    <div className="bg-white border rounded-xl p-6 shadow-sm space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">Dashboard Update Scheduler</h2>
        <div className={`px-3 py-1 rounded-full text-sm ${settings.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {settings.enabled ? 'Active' : 'Paused'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Toggle + Off Duration */}
        <div>
          <label className="block text-sm font-medium mb-2">Auto Updates</label>
          <div className="flex items-center gap-4">
            <button
              onClick={() => updateSettings({ action: "toggle", off_duration_minutes: offDuration })}
              disabled={loading}
              className={`px-5 py-2 rounded-lg ${settings.enabled ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'} text-white`}
            >
              {settings.enabled ? 'Pause Updates' : 'Resume Updates'}
            </button>

            {!settings.enabled && (
              <div className="flex items-center gap-2">
                <label>Pause for:</label>
                <input
                  type="number"
                  min="5"
                  value={offDuration}
                  onChange={e => setOffDuration(Number(e.target.value))}
                  className="w-20 border rounded px-2 py-1"
                />
                <span>minutes</span>
              </div>
            )}
          </div>
        </div>

        {/* Interval Change */}
        <div>
          <label className="block text-sm font-medium mb-2">Update Every</label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min="1"
              max="60"
              value={newInterval}
              onChange={e => setNewInterval(Number(e.target.value))}
              className="w-20 border rounded px-2 py-1"
            />
            <span>minutes</span>
            <button
              onClick={() => updateSettings({ interval_minutes: newInterval })}
              disabled={loading || newInterval === settings.intervalMinutes}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Apply
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">Current: every {settings.intervalMinutes} min</p>
        </div>
      </div>

      {settings.resumeInMinutes && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <p className="text-yellow-800">
            Scheduler paused. Auto-resume in <strong>{settings.resumeInMinutes} minutes</strong>.
          </p>
        </div>
      )}
    </div>
  )
}