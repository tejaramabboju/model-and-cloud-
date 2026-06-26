export default function StatsCard({ title, value, icon: Icon, iconBg = '#F3E8FF', iconColor = '#7C3AED', trendText, trendColor = '#6EE7B7' }) {
  return (
    <div className="kpi-card">
      <div className="kpi-top">
        <div className="kpi-icon" style={{ backgroundColor: iconBg }}>
          {Icon && <Icon style={{ width: 18, height: 18, color: iconColor }} />}
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
