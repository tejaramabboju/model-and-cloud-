import { useState, useEffect } from 'react';
import { ChartBar as BarChart3, FileText, DollarSign, PiggyBank, Target } from 'lucide-react';
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

const CHART_COLORS = ['#C084FC', '#67E8F9', '#6EE7B7', '#FCA5A5', '#FDE68A', '#F59E0B', '#818CF8', '#A78BFA'];

function SkeletonCard() {
  return (
    <div className="kpi-card">
      <div className="skeleton w-8 h-8 mb-3 rounded-xl" />
      <div className="skeleton w-20 h-6 mb-2" />
      <div className="skeleton w-14 h-2" />
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, padding: '10px 14px', fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
      <p style={{ color: '#1E1B4B', fontWeight: 700, marginBottom: 4 }}>{label || payload[0]?.name}</p>
      <p style={{ color: '#6B7280' }}>
        Count: <span style={{ color: '#7C3AED', fontWeight: 700 }}>{payload[0]?.value}</span>
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
      <div className="mb-6">
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
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
              iconBg="#F5F3FF"
              iconColor="#7C3AED"
              trendText="+6 this week"
              trendColor="#059669"
            />
            <StatsCard
              title="Monthly spend"
              value={`$${(stats?.total_monthly_spend ?? 0).toLocaleString()}`}
              icon={DollarSign}
              iconBg="#ECFEFF"
              iconColor="#0891B2"
              trendText="estimated"
              trendColor="#6B7280"
            />
            <StatsCard
              title="Total savings"
              value={`$${(stats?.total_savings ?? 0).toLocaleString()}`}
              icon={PiggyBank}
              iconBg="#FEF2F2"
              iconColor="#DC2626"
              trendText="vs baseline"
              trendColor="#059669"
            />
            <StatsCard
              title="Avg confidence"
              value={`${Math.round(stats?.avg_confidence ?? 0)}%`}
              icon={Target}
              iconBg="#ECFDF5"
              iconColor="#059669"
              trendText="+3% vs last month"
              trendColor="#059669"
            />
          </>
        )}
      </div>

      {/* Charts */}
      {!loading && (modelData.length > 0 || cloudData.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {modelData.length > 0 && (
            <div id="model-distribution-chart" className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#1E1B4B' }}>Model distribution</span>
                <span style={{ fontSize: '11px', color: '#9CA3AF' }}>by recommendation count</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={modelData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#6B7280', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    angle={-15}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis
                    tick={{ fill: '#6B7280', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(192, 132, 252, 0.06)' }} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={40}>
                    {modelData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {cloudData.length > 0 && (
            <div id="cloud-distribution-chart" className="glass-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
                <span style={{ fontSize: '14px', fontWeight: 700, color: '#1E1B4B' }}>Cloud distribution</span>
                <span style={{ fontSize: '11px', color: '#9CA3AF' }}>by provider</span>
              </div>
              <ResponsiveContainer width="100%" height={220}>
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
                    wrapperStyle={{ fontSize: '11px', color: '#6B7280' }}
                    iconType="circle"
                    iconSize={8}
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
          <BarChart3 style={{ width: 40, height: 40, color: '#C084FC', margin: '0 auto 16px' }} />
          <p style={{ fontSize: 14, fontWeight: 700, color: '#6B7280', marginBottom: 6 }}>No data yet</p>
          <p style={{ fontSize: 13, color: '#9CA3AF' }}>
            Submit your first use case to start seeing analytics.
          </p>
        </div>
      )}
    </div>
  );
}
