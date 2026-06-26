import { useState, useMemo, Fragment } from 'react';
import { Search, ChevronDown, ChevronUp, FileText, Calendar, Brain, Cloud, DollarSign, Gauge } from 'lucide-react';
import TriageBadge from './TriageBadge';
import ComplianceBadge from './ComplianceBadge';

export default function HistoryTable({ useCases, onSelectUseCase }) {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');

  const filtered = useMemo(() => {
    if (!useCases) return [];
    let result = useCases;

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (uc) =>
          uc.description?.toLowerCase().includes(q) ||
          uc.recommendation?.recommended_model?.toLowerCase().includes(q) ||
          uc.recommendation?.recommended_cloud?.toLowerCase().includes(q)
      );
    }

    result = [...result].sort((a, b) => {
      let aVal, bVal;
      switch (sortBy) {
        case 'created_at':
          aVal = new Date(a.created_at || 0).getTime();
          bVal = new Date(b.created_at || 0).getTime();
          break;
        case 'cost':
          aVal = a.recommendation?.estimated_monthly_cost || 0;
          bVal = b.recommendation?.estimated_monthly_cost || 0;
          break;
        case 'confidence':
          aVal = a.recommendation?.confidence_score || 0;
          bVal = b.recommendation?.confidence_score || 0;
          break;
        default:
          aVal = a[sortBy] || '';
          bVal = b[sortBy] || '';
      }
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [useCases, search, sortBy, sortDir]);

  const toggleSort = (col) => {
    if (sortBy === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(col);
      setSortDir('desc');
    }
  };

  const SortIcon = ({ col }) => {
    if (sortBy !== col) return null;
    return sortDir === 'asc' ? (
      <ChevronUp className="w-3 h-3" />
    ) : (
      <ChevronDown className="w-3 h-3" />
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (!useCases || useCases.length === 0) {
    return (
      <div id="history-empty" className="glass-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
        <FileText style={{ width: 36, height: 36, color: '#3d4260', margin: '0 auto 14px' }} />
        <p style={{ fontSize: 14, fontWeight: 600, color: '#5c6189', marginBottom: 6 }}>No advisory history yet</p>
        <p style={{ fontSize: 12, color: '#3d4260' }}>
          Submit your first use case to see results here.
        </p>
      </div>
    );
  }

  return (
    <div id="history-table-wrapper" className="space-y-4 animate-slide-up">
      {/* Search */}
      <div style={{ position: 'relative' }}>
        <Search style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 14, height: 14, color: '#5c6189' }} />
        <input
          id="history-search"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search use cases, models, or providers..."
          style={{ width: '100%', background: '#0A0C12', border: '0.5px solid #2a2d3a', borderRadius: 8, paddingLeft: 38, paddingRight: 16, paddingTop: 9, paddingBottom: 9, fontSize: 12.5, color: '#c9d1e8', outline: 'none' }}
          onFocus={e => e.target.style.borderColor = '#6366F1'}
          onBlur={e => e.target.style.borderColor = '#2a2d3a'}
        />
      </div>

      {/* Table */}
      <div id="history-table-wrapper-inner" className="glass-card" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '0.5px solid #1e2130', background: '#0d0f1a' }}>
                {[
                  { col: 'created_at', label: 'Date' },
                  { col: 'description', label: 'Description' },
                  { col: 'triage', label: 'Complexity' },
                  { col: 'model', label: 'Model' },
                  { col: 'cloud', label: 'Cloud' },
                  { col: 'cost', label: 'Cost' },
                  { col: 'confidence', label: 'Confidence' },
                ].map(({ col, label }) => (
                  <th
                    key={col}
                    onClick={() => toggleSort(col)}
                    style={{ padding: '10px 16px', fontSize: 9.5, fontWeight: 600, color: '#5c6189', textTransform: 'uppercase', letterSpacing: '0.8px', cursor: 'pointer', textAlign: col === 'cost' ? 'right' : 'left', whiteSpace: 'nowrap' }}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      {label}
                      <SortIcon col={col} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((uc, idx) => {
                const rec = uc.recommendation || {};

                return (
                  <tr
                    key={uc.id ?? idx}
                    id={`history-row-${uc.id ?? idx}`}
                    onClick={() => onSelectUseCase(uc)}
                    style={{ borderBottom: '0.5px solid #1e2130', cursor: 'pointer', background: idx % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent', transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.05)'}
                    onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? 'rgba(255,255,255,0.01)' : 'transparent'}
                  >
                    <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', color: '#4b5280', fontSize: 11.5 }}>
                      {formatDate(uc.created_at)}
                    </td>
                    <td style={{ padding: '12px 16px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#c9d1e8', fontWeight: 500, fontSize: 12 }}>
                      {uc.description}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      {uc.triage && <TriageBadge classification={typeof uc.triage === 'string' ? uc.triage : uc.triage.classification} />}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#a5b4fc', fontWeight: 500, fontSize: 12 }}>
                      {rec.recommended_model || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#818cf8', fontSize: 12 }}>
                      {rec.recommended_cloud || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', color: '#c9d1e8', fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
                      {rec.estimated_monthly_cost != null
                        ? `$${Number(rec.estimated_monthly_cost).toLocaleString()}`
                        : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: 12 }}>
                      {rec.confidence_score != null ? (
                        <span
                          style={{ fontWeight: 600, fontFamily: 'JetBrains Mono, monospace', color: rec.confidence_score >= 80 ? '#4ade80' : rec.confidence_score >= 60 ? '#f97316' : '#f87171' }}
                        >
                          {Math.round(rec.confidence_score)}%
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <p style={{ fontSize: 11, color: '#3d4260', textAlign: 'center' }}>
        Showing {filtered.length} of {useCases.length} results
      </p>
    </div>
  );
}
