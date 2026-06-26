export default function StatsCard({ title, value, icon: Icon, iconBg = '#1a1d2e', iconColor = '#818cf8', trendText, trendColor = '#4ade80' }) {
  return (
    <div className="kpi-card">
      <div className="kpi-top">
        <div className="kpi-icon" style={{ backgroundColor: iconBg }}>
          {Icon && <Icon style={{ width: 15, height: 15, color: iconColor }} />}
        </div>
        {trendText && (
          <span className="kpi-trend" style={{ color: trendColor }}>
            {trendText}
          </span>
        )}
      </div>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{title}</div>
    </div>
  );
}
