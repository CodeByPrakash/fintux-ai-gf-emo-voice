import { useState, useEffect } from 'react';
import { apiFetch } from '../utils/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function AnalyticsPage() {
  const [overview, setOverview] = useState(null);
  const [moodHistory, setMoodHistory] = useState([]);
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    apiFetch('/analytics/overview').then(setOverview).catch(() => {});
    apiFetch('/analytics/mood-history?limit=30').then(setMoodHistory).catch(() => {});
    apiFetch('/analytics/activity').then(setActivity).catch(() => {});
  }, []);

  const stats = overview || { total_messages: 0, total_sessions: 0, avg_response_time_ms: 0, memories_stored: 0 };

  const tooltipStyle = {
    background: '#1f1a30',
    border: '2px solid #3b3259',
    borderRadius: '12px',
    boxShadow: '4px 4px 0px #060509',
    color: '#fcf8fa',
    fontFamily: 'Outfit, sans-serif',
    fontSize: '12px',
    fontWeight: '700'
  };

  return (
    <div className="dashboard-page">
      <div>
        <h1>NEURAL & AFFECTION TELEMETRY</h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Live metrics tracking connection depth, response latencies, and emotional intimacy over time.
        </p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Messages</span>
            <span style={{ fontSize: 16 }}>💬</span>
          </div>
          <span className="stat-value" style={{ color: 'var(--accent)' }}>
            {stats.total_messages}
          </span>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Heart Sessions</span>
            <span style={{ fontSize: 16 }}>⏳</span>
          </div>
          <span className="stat-value" style={{ color: 'var(--accent-violet)' }}>
            {stats.total_sessions}
          </span>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Avg Latency</span>
            <span style={{ fontSize: 16 }}>⚡</span>
          </div>
          <span className="stat-value" style={{ color: 'var(--accent-amber)' }}>
            {Math.round(stats.avg_response_time_ms)}ms
          </span>
        </div>

        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="stat-label">Memories Stored</span>
            <span style={{ fontSize: 16 }}>🧠</span>
          </div>
          <span className="stat-value" style={{ color: 'var(--accent-mint)' }}>
            {stats.memories_stored}
          </span>
        </div>
      </div>

      <div className="chart-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3>AFFECTION & ENERGY RHYTHMS</h3>
          <div style={{ display: 'flex', gap: 14, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: '#f472b6' }}>● Mood</span>
            <span style={{ color: '#fbbf24' }}>● Energy</span>
            <span style={{ color: '#a78bfa' }}>● Bond</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={moodHistory}>
            <XAxis dataKey="timestamp" tick={false} stroke="#4a3e6d" />
            <YAxis domain={[0, 1]} stroke="#4a3e6d" />
            <Tooltip contentStyle={tooltipStyle} />
            <Line type="monotone" dataKey="mood" stroke="#f472b6" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="energy" stroke="#fbbf24" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="attachment" stroke="#a78bfa" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-section">
        <h3>CHAT ACTIVITY DISTRIBUTION</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={activity}>
            <XAxis dataKey="hour" stroke="#4a3e6d" />
            <YAxis stroke="#4a3e6d" />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill="#a78bfa" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
