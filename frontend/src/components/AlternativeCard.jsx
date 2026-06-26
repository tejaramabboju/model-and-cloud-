import { Cloud, MapPin, DollarSign } from 'lucide-react';

export default function AlternativeCard({ alternative, index }) {
  if (!alternative) return null;

  return (
    <div
      id={`alternative-card-${index}`}
      className="glass-card glass-card-hover p-5 transition-all duration-200"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="w-6 h-6 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-[0.65rem] font-bold text-slate-600">
          {index + 2}
        </span>
        <span className="text-xs font-medium text-slate-500">Alternative Option</span>
      </div>

      <h4 className="text-sm font-semibold text-slate-950 mb-2">{alternative.model}</h4>

      <div className="space-y-1.5 mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Cloud className="w-3 h-3" />
          <span>{alternative.cloud}</span>
        </div>
        {alternative.region && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <MapPin className="w-3 h-3" />
            <span>{alternative.region}</span>
          </div>
        )}
        {alternative.estimated_monthly_cost != null && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <DollarSign className="w-3 h-3 text-slate-500" />
            <span className="font-mono-numbers">${Number(alternative.estimated_monthly_cost).toLocaleString()}/mo</span>
          </div>
        )}
      </div>

      {alternative.trade_off && (
        <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-800 pt-3">
          {alternative.trade_off}
        </p>
      )}
    </div>
  );
}
