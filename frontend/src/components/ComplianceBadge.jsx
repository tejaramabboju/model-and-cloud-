import { ShieldCheck, ShieldX, ShieldAlert } from 'lucide-react';

const statusConfig = {
  pass: {
    className: 'badge-emerald',
    icon: ShieldCheck,
  },
  fail: {
    className: 'badge-rose',
    icon: ShieldX,
  },
  warning: {
    className: 'badge-amber',
    icon: ShieldAlert,
  },
};

export default function ComplianceBadge({ flag, status, detail }) {
  const config = statusConfig[status] || statusConfig.warning;
  const Icon = config.icon;

  return (
    <div className="tooltip-wrapper inline-flex">
      <span
        id={`compliance-badge-${flag?.toLowerCase().replace(/\s+/g, '-')}`}
        className={`badge ${config.className}`}
      >
        <Icon className="w-3 h-3" />
        {flag}
      </span>
      {detail && (
        <span className="tooltip-text">{detail}</span>
      )}
    </div>
  );
}
