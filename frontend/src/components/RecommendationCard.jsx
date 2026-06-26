import { useState } from 'react';
import { CircleCheck as CheckCircle, TriangleAlert as AlertTriangle, Circle as XCircle, Shield, DollarSign, Code, Server, Layers, Lock, ChevronDown, ChevronRight, Zap, ExternalLink, TrendingDown } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer
} from 'recharts';

const COLORS = ['#C084FC', '#67E8F9', '#6EE7B7', '#FCA5A5', '#FDE68A', '#F59E0B'];

const C = {
  bg: '#FFFFFF',
  card: '#FFFFFF',
  card2: '#FAFAFA',
  border: '#E5E7EB',
  accent: '#7C3AED',
  accentSoft: '#F5F3FF',
  cyan: '#0891B2',
  text: '#1E1B4B',
  muted: '#6B7280',
  muted2: '#4B5563',
  green: '#059669',
  amber: '#B45309',
  red: '#DC2626',
};

function StatusIcon({ status, size = 14 }) {
  if (status === 'pass') return <CheckCircle size={size} color={C.green} />;
  if (status === 'warning') return <AlertTriangle size={size} color={C.amber} />;
  return <XCircle size={size} color={C.red} />;
}

function Badge({ children, color = C.accent, bg = C.accentSoft }) {
  return (
    <span style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: bg, color, border: `1px solid ${color}33` }}>
      {children}
    </span>
  );
}

function SectionEmpty({ msg }) {
  return <p style={{ color: C.muted, fontSize: 14, fontStyle: 'italic', margin: '20px 0' }}>{msg || 'Information not available for this recommendation.'}</p>;
}

function OverviewTab({ rec, triage }) {
  const confidence = rec?.confidence_score || 0;
  const circumference = 2 * Math.PI * 36;
  const strokeDash = (confidence / 100) * circumference;
  const confColor = confidence >= 75 ? C.green : confidence >= 50 ? C.amber : C.red;

  const complexityColors = { Simple: C.green, Moderate: C.amber, Complex: C.red };
  const classColor = complexityColors[triage?.classification] || C.amber;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 12 }}>
        {/* Model Card */}
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 14, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.accent, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>Recommended Model</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: C.text, marginBottom: 4 }}>{rec?.recommended_model || '—'}</div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 12 }}>{rec?.model_provider || ''}</div>
          {rec?.model_strengths?.slice(0, 3).map((s, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 5 }}>
              <span style={{ color: C.green, marginTop: 2, fontSize: 14 }}>✓</span>
              <span style={{ fontSize: 13, color: C.muted2, lineHeight: 1.5 }}>{s}</span>
            </div>
          ))}
          {rec?.model_limitations?.slice(0, 1).map((l, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 5 }}>
              <span style={{ color: C.amber, marginTop: 2, fontSize: 14 }}>⚠</span>
              <span style={{ fontSize: 13, color: C.muted, lineHeight: 1.5 }}>{l}</span>
            </div>
          ))}
        </div>

        {/* Cloud Card */}
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 14, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.cyan, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>Cloud Platform</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: C.text, marginBottom: 4 }}>{rec?.recommended_cloud || '—'}</div>
          <div style={{ fontSize: 13, color: C.muted, marginBottom: 12 }}>{rec?.recommended_region || rec?.region || ''}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {(rec?.cloud_services || []).slice(0, 4).map((svc, i) => {
              const cxColor = { Easy: C.green, Medium: C.amber, Advanced: C.red }[svc.setup_complexity] || C.muted;
              return (
                <span key={i} style={{ padding: '4px 10px', borderRadius: 14, fontSize: 11, fontWeight: 600, background: `${cxColor}15`, color: cxColor, border: `1px solid ${cxColor}30` }}>
                  {svc.service_name}
                </span>
              );
            })}
            {(rec?.cloud_services || []).length > 4 && (
              <span style={{ fontSize: 11, color: C.muted, padding: '4px 6px' }}>+{rec.cloud_services.length - 4} more</span>
            )}
          </div>
        </div>

        {/* Confidence Ring */}
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 14, padding: '18px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minWidth: 100 }}>
          <svg width={88} height={88} style={{ marginBottom: 4 }}>
            <circle cx={44} cy={44} r={36} fill="none" stroke={C.border} strokeWidth={6} />
            <circle cx={44} cy={44} r={36} fill="none" stroke={confColor} strokeWidth={6}
              strokeDasharray={`${strokeDash} ${circumference}`} strokeLinecap="round"
              transform="rotate(-90 44 44)" />
            <text x={44} y={44} textAnchor="middle" dominantBaseline="middle" fill={confColor} fontSize={18} fontWeight={800}>{confidence}</text>
            <text x={44} y={58} textAnchor="middle" dominantBaseline="middle" fill={C.muted} fontSize={9}>/100</text>
          </svg>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence</div>
        </div>
      </div>

      {/* Triage + Rationale */}
      <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 14, padding: '18px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
          <Badge color={classColor} bg={`${classColor}18`}>{triage?.classification || 'Moderate'} complexity</Badge>
          {rec?.missing_info_impact && rec.missing_info_impact !== 'none' && (
            <Badge color={C.amber} bg={`${C.amber}15`}>Assumptions made</Badge>
          )}
          {rec?.within_budget === true && <Badge color={C.green} bg={`${C.green}15`}>Within budget</Badge>}
          {rec?.within_budget === false && <Badge color={C.red} bg={`${C.red}15`}>May exceed budget</Badge>}
        </div>
        <div style={{ fontSize: 14, color: C.muted2, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
          {rec?.model_rationale || rec?.rationale || 'No rationale provided.'}
        </div>
        {rec?.cloud_rationale && (
          <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.border}`, fontSize: 14, color: C.muted, lineHeight: 1.6 }}>
            <strong style={{ color: C.muted2 }}>Cloud reasoning:</strong> {rec.cloud_rationale}
          </div>
        )}
      </div>
    </div>
  );
}

function CostTab({ rec }) {
  const cb = rec?.cost_breakdown;
  if (!cb) return <SectionEmpty msg="Cost breakdown not available for this recommendation." />;

  const items = cb.cost_breakdown_items || [];
  const chartData = items.slice(0, 6).map(it => ({ name: it.item.length > 22 ? it.item.slice(0, 22) + '…' : it.item, value: it.monthly_usd }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
        {[
          { label: 'LLM API cost', value: `$${(cb.llm_cost_monthly || 0).toFixed(2)}/mo`, color: C.accent },
          { label: 'Cloud infra', value: `$${(cb.cloud_infra_cost_monthly || 0).toFixed(2)}/mo`, color: C.cyan },
          { label: 'Total monthly', value: `$${(cb.total_estimated_monthly || 0).toFixed(2)}`, color: C.text },
          { label: 'vs GPT-4o baseline', value: `–$${Math.max(0, cb.estimated_savings || 0).toFixed(2)}`, color: C.green },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '14px 16px', textAlign: 'center' }}>
            <div style={{ fontSize: 10, color: C.muted, fontWeight: 700, textTransform: 'uppercase', marginBottom: 5 }}>{label}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: 'JetBrains Mono, monospace' }}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {cb.llm_cost_per_1k_requests > 0 && (
          <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '12px 16px', display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 10, color: C.muted, fontWeight: 600 }}>Per 1,000 requests</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: C.accent, fontFamily: 'JetBrains Mono, monospace' }}>${cb.llm_cost_per_1k_requests.toFixed(4)}</span>
          </div>
        )}
        {cb.llm_cost_per_user != null && (
          <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '12px 16px', display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 10, color: C.muted, fontWeight: 600 }}>Per user per month</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: C.cyan, fontFamily: 'JetBrains Mono, monospace' }}>${cb.llm_cost_per_user.toFixed(2)}</span>
          </div>
        )}
        {cb.baseline_comparison > 0 && (
          <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '12px 16px', display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 10, color: C.muted, fontWeight: 600 }}>GPT-4o baseline</span>
            <span style={{ fontSize: 16, fontWeight: 700, color: C.muted2, fontFamily: 'JetBrains Mono, monospace' }}>${cb.baseline_comparison.toFixed(2)}/mo</span>
          </div>
        )}
        {cb.estimated_savings > 0 && (
          <div style={{ background: `${C.green}10`, border: `1px solid ${C.green}30`, borderRadius: 12, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingDown size={18} color={C.green} />
            <div>
              <div style={{ fontSize: 10, color: C.green, fontWeight: 600 }}>You save</div>
              <div style={{ fontSize: 16, fontWeight: 800, color: C.green, fontFamily: 'JetBrains Mono, monospace' }}>${cb.estimated_savings.toFixed(2)}/mo ({Math.round(cb.estimated_savings / Math.max(cb.baseline_comparison, 1) * 100)}%)</div>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        {/* Table */}
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: `1px solid ${C.border}`, fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase' }}>Cost Breakdown</div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {items.map((it, i) => (
                <tr key={i} style={{ borderBottom: i < items.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                  <td style={{ padding: '10px 16px', fontSize: 13, color: C.muted2 }}>{it.item}</td>
                  <td style={{ padding: '10px 16px', fontSize: 13, fontWeight: 700, color: C.text, textAlign: 'right', fontFamily: 'JetBrains Mono, monospace' }}>${it.monthly_usd.toFixed(2)}</td>
                </tr>
              ))}
              {items.length > 0 && (
                <tr style={{ background: C.accentSoft }}>
                  <td style={{ padding: '12px 16px', fontSize: 13, fontWeight: 700, color: C.muted2 }}>Total</td>
                  <td style={{ padding: '12px 16px', fontSize: 14, fontWeight: 800, color: C.accent, textAlign: 'right', fontFamily: 'JetBrains Mono, monospace' }}>${(cb.total_estimated_monthly || 0).toFixed(2)}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Chart */}
        {chartData.length > 0 && (
          <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 10 }}>Cost by Service</div>
            <div style={{ height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: C.muted }} />
                  <YAxis tick={{ fontSize: 9, fill: C.muted }} />
                  <Tooltip
                    contentStyle={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
                    formatter={v => [`$${v.toFixed(2)}`, 'Monthly']}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={30}>
                    {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {cb.assumptions?.length > 0 && (
        <div style={{ background: `${C.amber}08`, border: `1px solid ${C.amber}25`, borderRadius: 10, padding: '14px 18px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.amber, marginBottom: 8, textTransform: 'uppercase' }}>Assumptions made</div>
          {cb.assumptions.map((a, i) => (
            <div key={i} style={{ fontSize: 13, color: C.muted2, marginBottom: 3 }}>• {a}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function DevGuideTab({ rec }) {
  const [openPhase, setOpenPhase] = useState(0);
  const phases = rec?.development_guide || [];
  if (!phases.length) return <SectionEmpty msg="Development guide not available." />;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {phases.map((phase, pi) => {
        const isOpen = openPhase === pi;
        return (
          <div key={pi} style={{ background: C.card2, border: `1px solid ${isOpen ? C.accent : C.border}`, borderRadius: 12, overflow: 'hidden', transition: 'border-color 0.15s' }}>
            <div
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 18px', cursor: 'pointer' }}
              onClick={() => setOpenPhase(isOpen ? -1 : pi)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 30, height: 30, borderRadius: '50%', background: isOpen ? C.accentSoft : '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800, color: isOpen ? C.accent : C.muted }}>
                  {phase.phase}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{phase.phase_name}</div>
                  <div style={{ fontSize: 12, color: C.muted }}>{phase.duration}</div>
                </div>
              </div>
              {isOpen ? <ChevronDown size={14} color={C.accent} /> : <ChevronRight size={14} color={C.muted} />}
            </div>
            {isOpen && (
              <div style={{ padding: '0 18px 18px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(phase.steps || []).map((step, si) => (
                  <div key={si} style={{ display: 'flex', gap: 12 }}>
                    <div style={{ minWidth: 24, height: 24, borderRadius: '50%', background: `${C.accent}20`, border: `1px solid ${C.accent}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: C.accent, marginTop: 1 }}>
                      {si + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 3 }}>{step.step}</div>
                      <div style={{ fontSize: 13, color: C.muted, lineHeight: 1.6, marginBottom: step.resources?.length ? 6 : 0 }}>{step.detail}</div>
                      {step.resources?.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {step.resources.map((r, ri) => (
                            <a key={ri} href={r} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: C.accent, textDecoration: 'none' }}>
                              <ExternalLink size={10} /> {r.replace('https://', '').split('/')[0]}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ArchitectureTab({ rec }) {
  if (!rec?.architecture_summary && !rec?.architecture_components?.length) return <SectionEmpty />;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {rec.architecture_summary && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 10 }}>System Overview</div>
          <div style={{ fontSize: 14, color: C.muted2, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{rec.architecture_summary}</div>
        </div>
      )}

      {rec.architecture_components?.length > 0 && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 10 }}>Components</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {rec.architecture_components.map((comp, i) => (
              <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '8px 14px', background: `${COLORS[i % COLORS.length]}15`, border: `1px solid ${COLORS[i % COLORS.length]}30`, borderRadius: 10, fontSize: 13, fontWeight: 600, color: COLORS[i % COLORS.length] }}>
                <Server size={10} /> {comp}
              </span>
            ))}
          </div>
        </div>
      )}

      {rec.data_flow?.length > 0 && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 12 }}>Request Flow</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {rec.data_flow.map((step, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <div style={{ minWidth: 24, height: 24, borderRadius: '50%', background: '#ECFEFF', border: '1px solid #67E8F9', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: C.cyan, marginTop: 1 }}>
                  {i + 1}
                </div>
                <div style={{ fontSize: 13, color: C.muted2, lineHeight: 1.5, paddingTop: 2 }}>{step.replace(/^\d+\.\s*/, '')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {rec.cloud_services?.length > 0 && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 12 }}>Cloud Services Needed</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {rec.cloud_services.map((svc, i) => {
              const cxColor = { Easy: C.green, Medium: C.amber, Advanced: C.red }[svc.setup_complexity] || C.muted;
              return (
                <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                  <span style={{ padding: '4px 10px', borderRadius: 8, fontSize: 10, fontWeight: 700, background: `${cxColor}15`, color: cxColor, minWidth: 60, textAlign: 'center', marginTop: 2 }}>{svc.setup_complexity}</span>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{svc.service_name}</div>
                    <div style={{ fontSize: 12, color: C.muted, marginBottom: 2 }}>{svc.purpose}</div>
                    <div style={{ fontSize: 13, color: C.muted2 }}>{svc.why_needed}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function ComplianceTab({ rec }) {
  const flags = rec?.compliance_flags || [];
  const secRecs = rec?.security_recommendations || [];
  if (!flags.length && !secRecs.length) return <SectionEmpty />;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {flags.length > 0 && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 12 }}>Compliance Checks</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {flags.map((f, i) => {
              const statusColor = f.status === 'pass' ? C.green : f.status === 'warning' ? C.amber : C.red;
              return (
                <div key={i} style={{ display: 'flex', gap: 10, padding: '12px 14px', background: `${statusColor}08`, border: `1px solid ${statusColor}25`, borderRadius: 10 }}>
                  <StatusIcon status={f.status} size={16} />
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{f.flag || f.check}</div>
                    <div style={{ fontSize: 13, color: C.muted2, marginTop: 2 }}>{f.detail}</div>
                    {f.note && f.status !== 'pass' && (
                      <div style={{ fontSize: 12, color: statusColor, marginTop: 4 }}>→ {f.note}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {secRecs.length > 0 && (
        <div style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 12, padding: '18px 20px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Lock size={12} /> Security Recommendations
          </div>
          {secRecs.map((r, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
              <Shield size={13} color={C.accent} style={{ marginTop: 2, flexShrink: 0 }} />
              <span style={{ fontSize: 13, color: C.muted2, lineHeight: 1.5 }}>{r}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AlternativesTab({ rec }) {
  const alts = rec?.alternatives || [];
  if (!alts.length) return <SectionEmpty msg="No alternative options generated for this recommendation." />;

  const recCost = rec?.estimated_monthly_cost || rec?.cost_breakdown?.total_estimated_monthly || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <p style={{ fontSize: 13, color: C.muted, margin: '0 0 4px' }}>
        These alternatives could be a better fit depending on your priorities.
      </p>
      {alts.map((alt, i) => {
        const altCost = alt.estimated_monthly_cost || 0;
        const costDiffUsd = alt.cost_diff_usd ?? (altCost - recCost);
        const costDiffPct = alt.cost_diff_pct;
        const diffColor = costDiffUsd > 0 ? C.amber : costDiffUsd < 0 ? C.green : C.muted;
        
        let diffStr = costDiffUsd > 0 ? `+$${costDiffUsd.toFixed(2)}/mo` : costDiffUsd < 0 ? `-$${Math.abs(costDiffUsd).toFixed(2)}/mo` : 'same cost';
        if (costDiffPct != null && costDiffPct !== 0) {
          diffStr += ` (${costDiffPct > 0 ? '+' : ''}${costDiffPct.toFixed(1)}%)`;
        }

        return (
          <div key={i} style={{ background: C.card2, border: `1px solid ${C.border}`, borderRadius: 14, padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 800, color: C.text }}>{alt.model}</div>
                <div style={{ fontSize: 13, color: C.muted }}>{alt.cloud} · {alt.region}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 18, fontWeight: 800, color: C.accent, fontFamily: 'JetBrains Mono, monospace' }}>${altCost.toFixed(2)}<span style={{ fontSize: 11, color: C.muted }}>/mo</span></div>
                <div style={{ fontSize: 12, color: diffColor, fontWeight: 600 }}>{diffStr}</div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>TRADE-OFF & DESCRIPTION</div>
              <div style={{ fontSize: 13, color: C.muted2, lineHeight: 1.6 }}>{alt.trade_off}</div>
            </div>

            {(alt.pros_of_switching?.length > 0 || alt.cons_of_switching?.length > 0) && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {alt.pros_of_switching?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: C.green, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 4 }}>Pros of Switching</div>
                    {alt.pros_of_switching.map((pro, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 13, color: C.muted2, marginBottom: 2 }}>
                        <span style={{ color: C.green }}>✓</span>
                        <span style={{ lineHeight: 1.4 }}>{pro}</span>
                      </div>
                    ))}
                  </div>
                )}
                {alt.cons_of_switching?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: C.red, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 4 }}>Cons of Switching</div>
                    {alt.cons_of_switching.map((con, idx) => (
                      <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 13, color: C.muted2, marginBottom: 2 }}>
                        <span style={{ color: C.red }}>✗</span>
                        <span style={{ lineHeight: 1.4 }}>{con}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {alt.changed_services?.length > 0 && (
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: C.cyan, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 4 }}>Infrastructure Service Changes</div>
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {alt.changed_services.map((svc, idx) => (
                    <div key={idx} style={{ fontSize: 12, color: C.muted2, fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ color: C.cyan }}>✦</span>
                      <span>{svc}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(alt.benchmark_gpqa != null || alt.benchmark_swe != null || alt.speed_tps != null || alt.max_context != null) && (
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 6 }}>Capability & Benchmark Metrics</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 8 }}>
                  {alt.benchmark_gpqa != null && (
                    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                      <span style={{ color: C.muted }}>GPQA (Reasoning):</span> <strong style={{ color: C.text }}>{alt.benchmark_gpqa}%</strong>
                    </div>
                  )}
                  {alt.benchmark_swe != null && (
                    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                      <span style={{ color: C.muted }}>SWE-Bench (Coding):</span> <strong style={{ color: C.text }}>{alt.benchmark_swe}%</strong>
                    </div>
                  )}
                  {alt.speed_tps != null && (
                    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                      <span style={{ color: C.muted }}>Speed (Throughput):</span> <strong style={{ color: C.text }}>{alt.speed_tps} t/s</strong>
                    </div>
                  )}
                  {alt.max_context != null && (
                    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                      <span style={{ color: C.muted }}>Context Window:</span> <strong style={{ color: C.text }}>{(alt.max_context / 1000).toFixed(0)}k</strong>
                    </div>
                  )}
                </div>
              </div>
            )}

            {alt.best_for && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, borderTop: `1px solid ${C.border}`, paddingTop: 8 }}>
                <span style={{ fontSize: 12, color: C.muted }}>Best for:</span>
                <Badge color={C.cyan} bg={`#ECFEFF`}>{alt.best_for}</Badge>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const TABS = [
  { id: 'overview', label: 'Overview', icon: Layers },
  { id: 'cost', label: 'Cost', icon: DollarSign },
  { id: 'guide', label: 'Dev Guide', icon: Code },
  { id: 'arch', label: 'Architecture', icon: Server },
  { id: 'compliance', label: 'Compliance', icon: Shield },
  { id: 'alternatives', label: 'Alternatives', icon: Zap },
];

export default function RecommendationCard({ recommendation, triage }) {
  const [activeTab, setActiveTab] = useState('overview');
  const rec = recommendation;

  if (!rec) return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 32, textAlign: 'center', color: C.muted }}>
      No recommendation available yet.
    </div>
  );

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.04)' }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${C.border}`, overflowX: 'auto', background: C.card2 }}>
        {TABS.map(tab => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '14px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none',
                background: active ? C.card : 'transparent', color: active ? C.text : C.muted,
                borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
                whiteSpace: 'nowrap', transition: 'all 0.15s',
              }}
            >
              <tab.icon style={{ width: 14, height: 14, display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div style={{ padding: '24px', overflowY: 'auto', maxHeight: 'calc(100vh - 220px)' }}>
        {activeTab === 'overview' && <OverviewTab rec={rec} triage={triage} />}
        {activeTab === 'cost' && <CostTab rec={rec} />}
        {activeTab === 'guide' && <DevGuideTab rec={rec} />}
        {activeTab === 'arch' && <ArchitectureTab rec={rec} />}
        {activeTab === 'compliance' && <ComplianceTab rec={rec} />}
        {activeTab === 'alternatives' && <AlternativesTab rec={rec} />}
      </div>
    </div>
  );
}
