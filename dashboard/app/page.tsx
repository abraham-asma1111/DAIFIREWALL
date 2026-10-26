'use client'

import { useState, useEffect } from 'react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_flows: 0,
    threats_detected: 0,
    false_positives: 0,
    uptime: 0,
    avg_latency: 0
  })

  const [recentFlows, setRecentFlows] = useState<any[]>([])

  useEffect(() => {
    // Fetch stats from API
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/stats')
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Dynamic AI Firewall</h1>
          <p className="text-gray-400">Real-time threat detection powered by reinforcement learning</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Flows"
            value={stats.total_flows.toLocaleString()}
            subtitle="Network connections"
            color="blue"
          />
          <StatCard
            title="Threats Detected"
            value={stats.threats_detected.toLocaleString()}
            subtitle="Attacks blocked"
            color="red"
          />
          <StatCard
            title="False Positives"
            value={stats.false_positives.toLocaleString()}
            subtitle="Safe traffic blocked"
            color="yellow"
          />
          <StatCard
            title="Avg Latency"
            value={`${stats.avg_latency.toFixed(2)}ms`}
            subtitle="Decision time"
            color="green"
          />
        </div>

        {/* System Status */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatusIndicator label="RL Agent" status="online" />
            <StatusIndicator label="Anomaly Detector" status="online" />
            <StatusIndicator label="Novelty Scorer" status="online" />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
          <div className="text-gray-400 text-center py-8">
            Connect to API to see live traffic detection
          </div>
        </div>

        {/* API Connection Info */}
        <div className="mt-8 p-4 bg-blue-900/30 border border-blue-500 rounded-lg">
          <p className="text-sm">
            <span className="font-semibold">Backend API:</span> http://localhost:8000
          </p>
          <p className="text-sm mt-1 text-gray-400">
            Start API: <code className="bg-gray-800 px-2 py-1 rounded">python src/api/main.py</code>
          </p>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, subtitle, color }: any) {
  const colors = {
    blue: 'bg-blue-900/30 border-blue-500',
    red: 'bg-red-900/30 border-red-500',
    yellow: 'bg-yellow-900/30 border-yellow-500',
    green: 'bg-green-900/30 border-green-500'
  }

  return (
    <div className={`${colors[color]} border rounded-lg p-6`}>
      <h3 className="text-gray-400 text-sm mb-2">{title}</h3>
      <div className="text-3xl font-bold mb-1">{value}</div>
      <p className="text-gray-500 text-xs">{subtitle}</p>
    </div>
  )
}

function StatusIndicator({ label, status }: any) {
  const isOnline = status === 'online'
  
  return (
    <div className="flex items-center space-x-3">
      <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
      <div>
        <div className="font-semibold">{label}</div>
        <div className="text-sm text-gray-400">{isOnline ? 'Online' : 'Offline'}</div>
      </div>
    </div>
  )
}
