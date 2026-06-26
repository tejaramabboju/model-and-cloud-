import { useState, useMemo } from 'react';
import { Search, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import TriageBadge from './TriageBadge';

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
        <FileText style={{ width: 36, height: 36, color: '#C084FC', margin: '0 auto 14px' }} />
        <p style={{ fontSize: 14, fontWeight: 700, color: '#4B5563', marginBottom: 6 }}>No advisory history yet</p>
        <p style={{ fontSize: 12, color: '#9CA3AF' }}>
          Submit your first use case to see results here.
        </p>
      </div>
    );
  }

  return (
    <div id="history-table-wrapper" className="space-y-4 animate-slide-up">
      {/* Search */}
      <div style={{ position: 'relative' }}>
        <Search style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', width: 14, height: 14, color: '#9CA3AF' }} />
        <input
          id="history-search"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search use cases, models, or providers..."
          style={{ width: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, paddingLeft: 38, paddingRight: 16, paddingTop: 10, paddingBottom: 10, fontSize: 13, color: '#1E1B4B', outline: 'none', boxShadow: '0 1px 4px rgba(0,0,0,0.02)' }}
          onFocus={e => { e.target.style.borderColor = '#7C3AED'; e.target.style.boxShadow = '0 0 0 3px rgba(124, 58, 237, 0.1)'; }}
          onBlur={e => { e.target.style.borderColor = '#E5E7EB'; e.target.style.boxShadow = '0 1px 4px rgba(0,0,0,0.02)'; }}
        />
      </div>

      {/* Table */}
      <div id="history-table-wrapper-inner" className="glass-card" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #E5E7EB', background: '#F5F3FF' }}>
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
                    style={{ padding: '12px 16px', fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.8px', cursor: 'pointer', textAlign: col === 'cost' ? 'right' : 'left', whiteSpace: 'nowrap' }}
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
                    style={{ borderBottom: '1px solid #E5E7EB', cursor: 'pointer', background: idx % 2 === 0 ? '#FFFFFF' : '#FAFAFA', transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#F5F3FF'}
                    onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? '#FFFFFF' : '#FAFAFA'}
                  >
                    <td style={{ padding: '14px 16px', whiteSpace: 'nowrap', color: '#6B7280', fontSize: 12 }}>
                      {formatDate(uc.created_at)}
                    </td>
                    <td style={{ padding: '14px 16px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#1E1B4B', fontWeight: 600, fontSize: 13 }}>
                      {uc.description}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {uc.triage && <TriageBadge classification={typeof uc.triage === 'string' ? uc.triage : uc.triage.classification} />}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#7C3AED', fontWeight: 600, fontSize: 13 }}>
                      {rec.recommended_model || '—'}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#0891B2', fontSize: 13 }}>
                      {rec.recommended_cloud || '—'}
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right', color: '#1E1B4B', fontFamily: 'JetBrains Mono, monospace', fontSize: 13 }}>
                      {rec.estimated_monthly_cost != null
                        ? `$${Number(rec.estimated_monthly_cost).toLocaleString()}`
                        : '—'}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13 }}>
                      {rec.confidence_score != null ? (
                        <span
                          style={{ fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', color: rec.confidence_score >= 80 ? '#059669' : rec.confidence_score >= 60 ? '#B45309' : '#DC2626' }}
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

      <p style={{ fontSize: 12, color: '#9CA3AF', textAlign: 'center' }}>
        Showing {filtered.length} of {useCases.length} results
      </p>
    </div>
  );
}
