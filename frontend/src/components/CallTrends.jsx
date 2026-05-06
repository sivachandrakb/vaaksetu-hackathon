import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

const SENTIMENT_COLORS = {
  distress:  '#ef4444',
  anger:     '#f97316',
  confusion: '#eab308',
  urgency:   '#dc2626',
  calm:      '#22c55e',
  fear:      '#a855f7',
}

export function HourlyTrendsChart({ data }) {
  if (!data?.length) return null
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Calls per Hour Today</p>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip
            formatter={(val, name) => [val, 'Calls']}
            labelFormatter={l => `Hour: ${l}`}
            contentStyle={{ fontSize: 11 }}
          />
          <Bar dataKey="count" fill="#1a56db" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function SentimentPieChart({ data }) {
  if (!data) return null
  const chartData = Object.entries(data).map(([key, val]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value: Math.round(val * 100),
    color: SENTIMENT_COLORS[key] || '#6b7280',
  }))
  return (
    <div>
      <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Sentiment Distribution</p>
      <ResponsiveContainer width="100%" height={160}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={55}
            label={({ name, value }) => `${name}: ${value}%`}
            labelLine={false}
          >
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={v => [`${v}%`, '']} contentStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
