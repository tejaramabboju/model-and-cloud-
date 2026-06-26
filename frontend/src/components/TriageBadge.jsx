import { Zap, AlertTriangle, Flame } from 'lucide-react';

const config = {
  Simple: {
    className: 'badge-emerald',
    icon: Zap,
  },
  Moderate: {
    className: 'badge-amber',
    icon: AlertTriangle,
  },
  Complex: {
    className: 'badge-rose',
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
