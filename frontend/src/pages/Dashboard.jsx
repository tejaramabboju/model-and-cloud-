import { useState, useEffect } from 'react';
import {
  BarChart3,
  FileText,
  DollarSign,
  PiggyBank,
  Target,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import StatsCard from '../components/StatsCard';
import { getDashboardStats } from '../api/client';

const CHART_COLORS = ['#6366F1', '#8b5cf6', '#22D3EE', '#4ade80', '#f97316', '#f87171', '#818CF8', '#67E8F9'];
const DARK_BG = '#0A0C12';
const DARK_BORDER = '#1e2130';
const DARK_GRID = '#1e2130';
const TICK_COLOR = '#5c6189';

function SkeletonCard() {
  return (
    <div className="kpi-card">
      <div className="skeleton w-7 h-7 mb-3 rounded-lg" />
      <div className="skeleton w-20 h-6 mb-2" />
      <div className="skeleton w-14 h-2" />
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#13152a', border: '0.5px solid #2a2d3a', borderRadius: 8, padding: '8px 12px', fontSize: 11 }}>
      <p style={{ color: '#e2e8f0', fontWeight: 600, marginBottom: 4 }}>{label || payload[0]?.name}</p>
      <p style={{ color: '#5c6189' }}>
        Count: <span style={{ color: '#a5b4fc', fontWeight: 600 }}>{payload[0]?.value}</span>
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const fetchStats = async () => {
      try {
        const res = await getDashboardStats();
        if (!cancelled) setStats(res.data);
      } catch (err) {
        if (!cancelled) setError('Failed to load dashboard stats.');
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchStats();
    return () => { cancelled = true; };
  }, []);

  const modelData = stats?.model_distribution
    ? stats.model_distribution.map((item) => ({ name: item.model, value: item.count }))
    : [];

  const cloudData = stats?.cloud_distribution
    ? stats.cloud_distribution.map((item) => ({ name: item.cloud, value: item.count }))
    : [];

  return (
    <div id="dashboard-page" className="animate-fade-in">
      {/* Page Header — title lives in Layout topbar; just add spacing */}
      <div className="mb-6">
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <StatsCard
              title="Total use cases"
              value={stats?.total_use_cases ?? 0}
              icon={FileText}
              iconBg="#1a1d2e"
              iconColor="#818cf8"
              trendText="+6 this week"
              trendColor="#4ade80"
            />
            <StatsCard
              title="Monthly spend"
              value={`$${(stats?.total_monthly_spend ?? 0).toLocaleString()}`}
              icon={DollarSign}
              iconBg="#0e1c20"
              iconColor="#22d3ee"
              trendText="estimated"
              trendColor="#5c6189"
            />
            <StatsCard
              title="Total savings"
              value={`$${(stats?.total_savings ?? 0).toLocaleString()}`}
              icon={PiggyBank}
              iconBg="#1a120a"
              iconColor="#f97316"
              trendText="vs baseline"
              trendColor="#4ade80"
            />
            <StatsCard
              title="Avg confidence"
              value={`${Math.round(stats?.avg_confidence ?? 0)}%`}
              icon={Target}
              iconBg="#0d1a0e"
              iconColor="#4ade80"
              trendText="+3% vs last month"
              trendColor="#4ade80"
            />
          </>
        )}
      </div>

      {/* Charts */}
      {!loading && (modelData.length > 0 || cloudData.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Model Distribution Bar Chart */}
          {modelData.length > 0 && (
            <div id="model-distribution-chart" className="glass-card" style={{ padding: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span style={{ fontSize: '11.5px', fontWeight: 500, color: '#e2e8f0' }}>Model distribution</span>
                <span style={{ fontSize: '9.5px', color: '#3d4260' }}>by recommendation count</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={modelData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={DARK_GRID} vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: TICK_COLOR, fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    angle={-15}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis
                    tick={{ fill: TICK_COLOR, fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)' }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
                    {modelData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Cloud Distribution Pie Chart */}
          {cloudData.length > 0 && (
            <div id="cloud-distribution-chart" className="glass-card" style={{ padding: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span style={{ fontSize: '11.5px', fontWeight: 500, color: '#e2e8f0' }}>Cloud distribution</span>
                <span style={{ fontSize: '9.5px', color: '#3d4260' }}>by provider</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={cloudData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                  >
                    {cloudData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ fontSize: '10px', color: TICK_COLOR }}
                    iconType="circle"
                    iconSize={7}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && modelData.length === 0 && cloudData.length === 0 && (stats?.total_use_cases ?? 0) === 0 && (
        <div className="glass-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <BarChart3 style={{ width: 40, height: 40, color: '#3d4260', margin: '0 auto 16px' }} />
          <p style={{ fontSize: 14, fontWeight: 600, color: '#5c6189', marginBottom: 6 }}>No data yet</p>
          <p style={{ fontSize: 12, color: '#3d4260' }}>
            Submit your first use case to start seeing analytics.
          </p>
        </div>
      )}
    </div>
  );
}
