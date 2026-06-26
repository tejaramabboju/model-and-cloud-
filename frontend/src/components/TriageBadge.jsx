import { Zap, TriangleAlert as AlertTriangle, Flame } from 'lucide-react';

const config = {
  Simple: {
    className: 'bg-emerald-100 text-emerald-700',
    icon: Zap,
  },
  Moderate: {
    className: 'bg-amber-100 text-amber-700',
    icon: AlertTriangle,
  },
  Complex: {
    className: 'bg-rose-100 text-rose-700',
    icon: Flame,
  },
};

export default function TriageBadge({ classification }) {
  const c = config[classification] || config.Moderate;
  const Icon = c.icon;

  return (
    <span id={`triage-badge-${classification?.toLowerCase()}`} className={`badge ${c.className}`}>
      <Icon className="w-3 h-3" />
      {classification}
    </span>
  );
}
