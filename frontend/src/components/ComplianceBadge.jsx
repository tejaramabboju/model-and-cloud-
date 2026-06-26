import { ShieldCheck, ShieldX, ShieldAlert } from 'lucide-react';

const statusConfig = {
  pass: {
    className: 'bg-emerald-100 text-emerald-700',
    icon: ShieldCheck,
  },
  fail: {
    className: 'bg-rose-100 text-rose-700',
    icon: ShieldX,
  },
  warning: {
    className: 'bg-amber-100 text-amber-700',
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
