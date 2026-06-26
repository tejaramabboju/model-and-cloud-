import { useState } from 'react';
import { SendHorizontal, ChevronDown, ChevronRight, Settings2 } from 'lucide-react';

const s = {
  form: { display: 'flex', flexDirection: 'column', gap: 20 },
  panel: { background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 2px 12px rgba(0,0,0,0.04)' },
  sectionHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', userSelect: 'none', marginBottom: 0 },
  sectionTitle: { fontSize: 13, fontWeight: 700, color: '#6B7280', letterSpacing: '0.04em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 },
  sectionBody: { marginTop: 18, display: 'flex', flexDirection: 'column', gap: 14 },
  label: { display: 'block', fontSize: 12, fontWeight: 600, color: '#6B7280', marginBottom: 5, letterSpacing: '0.02em' },
  input: { width: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 14px', color: '#1E1B4B', fontSize: 13, outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box', transition: 'border-color 0.2s, box-shadow 0.2s' },
  select: { width: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 14px', color: '#1E1B4B', fontSize: 13, outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box', cursor: 'pointer', transition: 'border-color 0.2s, box-shadow 0.2s' },
  textarea: { width: '100%', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 16px', color: '#1E1B4B', fontSize: 14, outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box', resize: 'vertical', minHeight: 120, transition: 'border-color 0.2s, box-shadow 0.2s' },
  row2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  radioGroup: { display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  radioBtn: (active) => ({
    padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: active ? '1.5px solid #7C3AED' : '1px solid #E5E7EB',
    background: active ? '#F5F3FF' : '#FFFFFF', color: active ? '#7C3AED' : '#6B7280', transition: 'all 0.15s'
  }),
  checkGroup: { display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  checkBtn: (active) => ({
    padding: '5px 12px', borderRadius: 16, fontSize: 12, fontWeight: 600, cursor: 'pointer', border: active ? '1.5px solid #22D3EE' : '1px solid #E5E7EB',
    background: active ? '#ECFEFF' : '#FFFFFF', color: active ? '#0891B2' : '#6B7280', transition: 'all 0.15s'
  }),
  charCount: { fontSize: 11, color: '#9CA3AF', textAlign: 'right', marginTop: 3, fontFamily: 'monospace' },
  hint: { fontSize: 11, color: '#9CA3AF', marginTop: 4, lineHeight: 1.4 },
  submitBtn: (loading, disabled) => ({
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: '13px 28px', background: disabled ? '#E5E7EB' : 'linear-gradient(135deg, #7C3AED, #6366F1)',
    color: disabled ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 12, fontSize: 14, fontWeight: 700,
    cursor: disabled ? 'not-allowed' : 'pointer', transition: 'all 0.2s', width: '100%', marginTop: 4,
    boxShadow: disabled ? 'none' : '0 4px 14px rgba(124, 58, 237, 0.3)'
  }),
  advToggle: { display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', background: '#F5F3FF', border: '1px dashed #C084FC', borderRadius: 8, cursor: 'pointer', color: '#7C3AED', fontSize: 12, fontWeight: 600, userSelect: 'none', width: 'fit-content' },
};

export default function UseCaseForm({ onSubmit, isLoading, initialDescription = '', initialStructuredFields = {} }) {
  const isScalePrefilled = initialStructuredFields.daily_requests || initialStructuredFields.number_of_users || initialStructuredFields.avg_input_tokens || initialStructuredFields.avg_output_tokens || initialStructuredFields.monthly_budget_usd;
  const isCompliancePrefilled = initialStructuredFields.data_sensitivity || initialStructuredFields.compliance_region || initialStructuredFields.compliance_standards?.length;
  const isTechPrefilled = initialStructuredFields.existing_cloud || initialStructuredFields.team_expertise || initialStructuredFields.streaming_needed || initialStructuredFields.fine_tuning_needed || initialStructuredFields.on_premise_required || initialStructuredFields.multimodal_needs || initialStructuredFields.high_availability;

  const [description, setDescription] = useState(initialDescription);
  const [projectName, setProjectName] = useState(initialStructuredFields.project_name || '');
  const [showAdvanced, setShowAdvanced] = useState(!!(isScalePrefilled || isCompliancePrefilled || isTechPrefilled));
  const [openSection, setOpenSection] = useState({
    scale: !!isScalePrefilled,
    compliance: !!isCompliancePrefilled,
    tech: !!isTechPrefilled
  });

  // Scale fields
  const [dailyRequests, setDailyRequests] = useState(() => {
    const val = initialStructuredFields.daily_requests;
    if (!val) return '';
    if (val === '500') return 'under_1k';
    if (val === '5000') return '1k_10k';
    if (val === '50000') return '10k_100k';
    if (val === '500000') return '100k_plus';
    return val;
  });
  const [avgInput, setAvgInput] = useState(() => {
    const val = initialStructuredFields.avg_input_tokens;
    if (!val) return '';
    if (val === '100') return 'short';
    if (val === '500') return 'medium';
    if (val === '2500') return 'long';
    if (val === '7500') return 'very_long';
    return val;
  });
  const [avgOutput, setAvgOutput] = useState(() => {
    const val = initialStructuredFields.avg_output_tokens;
    if (!val) return '';
    if (val === '50') return 'short';
    if (val === '250') return 'medium';
    if (val === '750') return 'long';
    return val;
  });
  const [monthlyBudget, setMonthlyBudget] = useState(initialStructuredFields.monthly_budget_usd || '');
  const [numUsers, setNumUsers] = useState(initialStructuredFields.number_of_users || '');

  // Compliance fields
  const [dataSensitivity, setDataSensitivity] = useState(initialStructuredFields.data_sensitivity || '');
  const [complianceRegion, setComplianceRegion] = useState(initialStructuredFields.compliance_region || '');
  const [complianceStandards, setComplianceStandards] = useState(initialStructuredFields.compliance_standards || []);

  // Tech fields
  const [cloudPref, setCloudPref] = useState(initialStructuredFields.existing_cloud || '');
  const [teamExpertise, setTeamExpertise] = useState(initialStructuredFields.team_expertise || '');
  const [specialNeeds, setSpecialNeeds] = useState(() => {
    const needs = [];
    if (initialStructuredFields.streaming_needed === true) needs.push('streaming');
    if (initialStructuredFields.fine_tuning_needed === true) needs.push('fine_tuning');
    if (initialStructuredFields.on_premise_required === true) needs.push('on_premise');
    if (initialStructuredFields.multimodal_needs === true) needs.push('multimodal');
    if (initialStructuredFields.high_availability === true) needs.push('high_availability');
    return needs;
  });

  const toggleCheck = (list, setList, val) => {
    setList(prev => prev.includes(val) ? prev.filter(v => v !== val) : [...prev, val]);
  };

  const toggleSection = (key) => setOpenSection(prev => ({ ...prev, [key]: !prev[key] }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!description.trim() || isLoading) return;

    // Map dropdown values to field values
    const drMap = { 'under_1k': '500', '1k_10k': '5000', '10k_100k': '50000', '100k_plus': '500000' };
    const inMap = { 'short': '100', 'medium': '500', 'long': '2500', 'very_long': '7500' };
    const outMap = { 'short': '50', 'medium': '250', 'long': '750' };
    const needsMap = { 'streaming': 'streaming_needed', 'fine_tuning': 'fine_tuning_needed', 'on_premise': 'on_premise_required', 'multimodal': 'multimodal_needs', 'high_availability': 'high_availability' };

    const specialNeedsFields = {};
    specialNeeds.forEach(n => {
      if (needsMap[n]) specialNeedsFields[needsMap[n]] = true;
    });

    const structuredFields = {
      ...(projectName ? { project_name: projectName } : {}),
      ...(dailyRequests ? { daily_requests: drMap[dailyRequests] || dailyRequests } : {}),
      ...(avgInput ? { avg_input_tokens: inMap[avgInput] || avgInput } : {}),
      ...(avgOutput ? { avg_output_tokens: outMap[avgOutput] || avgOutput } : {}),
      ...(monthlyBudget ? { monthly_budget_usd: parseFloat(monthlyBudget) } : {}),
      ...(numUsers ? { number_of_users: parseInt(numUsers) } : {}),
      ...(dataSensitivity ? { data_sensitivity: dataSensitivity } : {}),
      ...(complianceRegion ? { compliance_region: complianceRegion } : {}),
      ...(complianceStandards.length ? { compliance_standards: complianceStandards } : {}),
      ...(cloudPref ? { existing_cloud: cloudPref } : {}),
      ...(teamExpertise ? { team_expertise: teamExpertise } : {}),
      ...specialNeedsFields,
    };

    onSubmit(description.trim(), Object.keys(structuredFields).length > 0 ? structuredFields : {});
  };

  const canSubmit = description.trim().length >= 5 && !isLoading;

  const SectionToggle = ({ sKey, title, icon }) => (
    <div style={s.sectionHeader} onClick={() => toggleSection(sKey)}>
      <span style={s.sectionTitle}>{icon} {title}</span>
      {openSection[sKey] ? <ChevronDown size={14} color="#374151" /> : <ChevronRight size={14} color="#374151" />}
    </div>
  );

  const RadioGroup = ({ options, value, onChange }) => (
    <div style={s.radioGroup}>
      {options.map(([val, label]) => (
        <button key={val} type="button" style={s.radioBtn(value === val)} onClick={() => onChange(value === val ? '' : val)}>
          {label}
        </button>
      ))}
    </div>
  );

  const CheckGroup = ({ options, value, onChange }) => (
    <div style={s.checkGroup}>
      {options.map(([val, label]) => (
        <button key={val} type="button" style={s.checkBtn(value.includes(val))} onClick={() => toggleCheck(value, onChange, val)}>
          {value.includes(val) ? '✓ ' : ''}{label}
        </button>
      ))}
    </div>
  );

  return (
    <form id="use-case-form" onSubmit={handleSubmit} style={s.form}>

      {/* ── Section A: Core Description ────────────────────────────────── */}
      <div style={s.panel}>
        <div style={{ marginBottom: 14 }}>
          <p style={{ fontSize: 16, fontWeight: 700, color: '#1E1B4B', margin: '0 0 4px' }}>Describe your use case</p>
          <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>
            What AI-powered product do you want to build? Include any details about users, data, or scale.
          </p>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={s.label}>Project Name <span style={{ color: '#9CA3AF' }}>(optional)</span></label>
          <input
            type="text"
            style={s.input}
            value={projectName}
            onChange={e => setProjectName(e.target.value)}
            placeholder="e.g. HR Chatbot, Medical Transcription Tool..."
            disabled={isLoading}
            onFocus={e => { e.target.style.borderColor = '#7C3AED'; e.target.style.boxShadow = '0 0 0 3px rgba(124, 58, 237, 0.1)'; }}
            onBlur={e => { e.target.style.borderColor = '#E5E7EB'; e.target.style.boxShadow = 'none'; }}
          />
        </div>

        <div>
          <label style={s.label}>Use case description <span style={{ color: '#7C3AED' }}>*</span></label>
          <textarea
            id="use-case-textarea"
            style={s.textarea}
            value={description}
            onChange={e => setDescription(e.target.value.slice(0, 2000))}
            placeholder="e.g. An AI-powered customer support chatbot for an e-commerce platform. It should handle order status queries, returns, and complaints. ~5,000 requests/day, EU users, GDPR compliance needed, budget around $300/month..."
            disabled={isLoading}
            maxLength={2000}
            onFocus={e => { e.target.style.borderColor = '#7C3AED'; e.target.style.boxShadow = '0 0 0 3px rgba(124, 58, 237, 0.1)'; }}
            onBlur={e => { e.target.style.borderColor = '#E5E7EB'; e.target.style.boxShadow = 'none'; }}
          />
          <div style={s.charCount}>{description.length} / 2000</div>
        </div>

        {/* Advanced toggle */}
        <div style={{ marginTop: 16 }}>
          <div style={s.advToggle} onClick={() => setShowAdvanced(v => !v)}>
            <Settings2 size={13} />
            {showAdvanced ? 'Hide' : 'Add'} optional details (budget, compliance, scale...)
            {showAdvanced ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </div>
        </div>
      </div>

      {/* ── Advanced Sections ────────────────────────────────────────── */}
      {showAdvanced && (<>

        {/* Section B: Scale & Usage */}
        <div style={s.panel}>
          <SectionToggle sKey="scale" title="Scale & Usage" icon="📊" />
          {openSection.scale && (
            <div style={s.sectionBody}>
              <div style={s.row2}>
                <div>
                  <label style={s.label}>Expected daily requests</label>
                  <select style={s.select} value={dailyRequests} onChange={e => setDailyRequests(e.target.value)} disabled={isLoading}>
                    <option value="">Not sure / skip</option>
                    <option value="under_1k">Under 1,000/day</option>
                    <option value="1k_10k">1,000 – 10,000/day</option>
                    <option value="10k_100k">10,000 – 100,000/day</option>
                    <option value="100k_plus">100,000+/day</option>
                  </select>
                </div>
                <div>
                  <label style={s.label}>Number of end users</label>
                  <input type="number" style={s.input} value={numUsers} onChange={e => setNumUsers(e.target.value)} placeholder="e.g. 500" disabled={isLoading} min="1" />
                </div>
              </div>
              <div style={s.row2}>
                <div>
                  <label style={s.label}>Average input length</label>
                  <select style={s.select} value={avgInput} onChange={e => setAvgInput(e.target.value)} disabled={isLoading}>
                    <option value="">Not sure / skip</option>
                    <option value="short">Short (&lt;200 tokens)</option>
                    <option value="medium">Medium (200–1K tokens)</option>
                    <option value="long">Long (1K–5K tokens)</option>
                    <option value="very_long">Very Long (5K+ tokens)</option>
                  </select>
                </div>
                <div>
                  <label style={s.label}>Average output length</label>
                  <select style={s.select} value={avgOutput} onChange={e => setAvgOutput(e.target.value)} disabled={isLoading}>
                    <option value="">Not sure / skip</option>
                    <option value="short">Short (&lt;100 tokens)</option>
                    <option value="medium">Medium (100–500 tokens)</option>
                    <option value="long">Long (500+ tokens)</option>
                  </select>
                </div>
              </div>
              <div>
                <label style={s.label}>Monthly budget (USD) <span style={{ color: '#374151' }}>optional</span></label>
                <input type="number" style={s.input} value={monthlyBudget} onChange={e => setMonthlyBudget(e.target.value)} placeholder="e.g. 300" disabled={isLoading} min="0" />
                <p style={s.hint}>Used to filter models and flag if the recommendation exceeds your budget.</p>
              </div>
            </div>
          )}
          {!openSection.scale && (
            <p style={{ fontSize: 12, color: '#374151', marginTop: 10, cursor: 'pointer' }} onClick={() => toggleSection('scale')}>
              Click to set daily requests, budget, and token estimates →
            </p>
          )}
        </div>

        {/* Section C: Compliance & Data */}
        <div style={s.panel}>
          <SectionToggle sKey="compliance" title="Compliance & Data" icon="🛡️" />
          {openSection.compliance && (
            <div style={s.sectionBody}>
              <div>
                <label style={s.label}>Data sensitivity</label>
                <RadioGroup
                  options={[
                    ['none', 'None (public)'],
                    ['low', 'Low (internal)'],
                    ['medium', 'Medium (PII)'],
                    ['high', 'High (financial)'],
                    ['critical', 'Critical (PHI/HIPAA)'],
                  ]}
                  value={dataSensitivity}
                  onChange={setDataSensitivity}
                />
              </div>
              <div>
                <label style={s.label}>User region</label>
                <select style={s.select} value={complianceRegion} onChange={e => setComplianceRegion(e.target.value)} disabled={isLoading}>
                  <option value="">Not specified</option>
                  <option value="global">Global</option>
                  <option value="EU">European Union (EU)</option>
                  <option value="USA">United States (USA)</option>
                  <option value="India">India</option>
                  <option value="UK">United Kingdom</option>
                  <option value="Australia">Australia</option>
                  <option value="Canada">Canada</option>
                </select>
              </div>
              <div>
                <label style={s.label}>Compliance standards needed</label>
                <CheckGroup
                  options={[['GDPR','GDPR'],['HIPAA','HIPAA'],['SOC2','SOC2'],['PCI_DSS','PCI-DSS'],['ISO27001','ISO 27001'],['FedRAMP','FedRAMP']]}
                  value={complianceStandards}
                  onChange={setComplianceStandards}
                />
              </div>
            </div>
          )}
          {!openSection.compliance && (
            <p style={{ fontSize: 12, color: '#374151', marginTop: 10, cursor: 'pointer' }} onClick={() => toggleSection('compliance')}>
              Click to set data sensitivity, region, and compliance standards →
            </p>
          )}
        </div>

        {/* Section D: Technical Preferences */}
        <div style={s.panel}>
          <SectionToggle sKey="tech" title="Technical Preferences" icon="⚙️" />
          {openSection.tech && (
            <div style={s.sectionBody}>
              <div>
                <label style={s.label}>Cloud provider preference</label>
                <RadioGroup
                  options={[['none','No preference'],['aws','AWS'],['gcp','GCP'],['azure','Azure']]}
                  value={cloudPref}
                  onChange={setCloudPref}
                />
              </div>
              <div>
                <label style={s.label}>Team expertise</label>
                <RadioGroup
                  options={[['beginner','Beginner'],['intermediate','Intermediate'],['expert','Expert']]}
                  value={teamExpertise}
                  onChange={setTeamExpertise}
                />
              </div>
              <div>
                <label style={s.label}>Special requirements</label>
                <CheckGroup
                  options={[
                    ['streaming','Streaming responses'],
                    ['fine_tuning','Fine-tuning required'],
                    ['on_premise','On-premise / VPC only'],
                    ['multimodal','Multimodal (image/audio/video)'],
                    ['high_availability','High availability (99.9%+)'],
                  ]}
                  value={specialNeeds}
                  onChange={setSpecialNeeds}
                />
              </div>
            </div>
          )}
          {!openSection.tech && (
            <p style={{ fontSize: 12, color: '#374151', marginTop: 10, cursor: 'pointer' }} onClick={() => toggleSection('tech')}>
              Click to set cloud preference, team expertise, and requirements →
            </p>
          )}
        </div>
      </>)}

      {/* Submit */}
      <button
        id="submit-use-case"
        type="submit"
        disabled={!canSubmit}
        style={s.submitBtn(isLoading, !canSubmit)}
      >
        {isLoading ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }} />
            Generating guidebook...
          </span>
        ) : (
          <>
            <SendHorizontal size={16} />
            Get AI recommendation
          </>
        )}
      </button>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        select option { background: #FFFFFF; color: #1E1B4B; }
        select:focus { border-color: #7C3AED; box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1); }
        input[type="number"]:focus { border-color: #7C3AED; box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1); }
      `}</style>
    </form>
  );
}
