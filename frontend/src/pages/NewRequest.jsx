import { useState, useRef, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Sparkles, Cpu, Cloud, ShieldCheck, Target, HelpCircle, ArrowRight, SkipForward } from 'lucide-react';
import UseCaseForm from '../components/UseCaseForm';
import LoadingSteps from '../components/LoadingSteps';
import RecommendationCard from '../components/RecommendationCard';
import StatsCard from '../components/StatsCard';
import ChatWidget, { formatMessageText } from '../components/ChatWidget';
import { submitUseCase, getDashboardStats, submitClarification } from '../api/client';

// ─── Clarification UI ─────────────────────────────────────────────────────────

function ClarificationPanel({ data, onSubmit, onSkip }) {
  const [answers, setAnswers] = useState({});
  const questions = data?.clarification_questions || [];
  const message = data?.clarification_message || '';

  return (
    <div style={{ background: '#0d1117', border: '1px solid #1e2535', borderRadius: 16, padding: '28px 32px', maxWidth: 620, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <HelpCircle size={20} color="#818cf8" />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: '#f1f5f9' }}>A few more details</h3>
          <p style={{ margin: 0, fontSize: 12, color: '#64748b' }}>Answer any you know — I'll use defaults for the rest</p>
        </div>
      </div>

      {message && (
        <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.7, marginBottom: 20, padding: '12px 14px', background: 'rgba(99,102,241,0.06)', borderRadius: 8, borderLeft: '3px solid #6366f1' }}>
          {formatMessageText(message)}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {questions.map((q, i) => (
          <div key={i}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#cbd5e1', marginBottom: 6 }}>
              {i + 1}. {q}
            </label>
            <input
              type="text"
              placeholder="Type your answer or leave blank to skip..."
              value={answers[i] || ''}
              onChange={e => setAnswers(prev => ({ ...prev, [i]: e.target.value }))}
              style={{ width: '100%', boxSizing: 'border-box', background: '#0b0f18', border: '1px solid #1e2535', borderRadius: 8, padding: '9px 12px', color: '#e2e8f0', fontSize: 13, outline: 'none', fontFamily: 'inherit' }}
            />
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
        <button
          onClick={() => {
            const answerMap = {};
            questions.forEach((q, i) => { if (answers[i]) answerMap[`question_${i}`] = answers[i]; });
            onSubmit(answerMap);
          }}
          style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '12px 20px', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
        >
          <ArrowRight size={16} /> Generate Recommendation
        </button>
        <button
          onClick={onSkip}
          style={{ padding: '12px 18px', display: 'flex', alignItems: 'center', gap: 6, background: '#111827', color: '#64748b', border: '1px solid #1e2535', borderRadius: 10, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
        >
          <SkipForward size={14} /> Skip
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function NewRequest() {
  const location = useLocation();
  const templateDescription = location.state?.templateDescription || '';
  const templateFields = location.state?.templateFields || {};

  // formState: idle | loading | clarifying | complete
  const [formState, setFormState] = useState('idle');
  const [result, setResult] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState(null);
  const [clarificationData, setClarificationData] = useState(null);

  const [kpis, setKpis] = useState({
    modelsCount: 50,
    providersCount: 3,
    checksCount: 312,
    accuracy: '91%',
  });

  const [chatMessages, setChatMessages] = useState([]);

  const stepTimerRef = useRef(null);

  const clearStepTimer = () => {
    if (stepTimerRef.current) { clearInterval(stepTimerRef.current); stepTimerRef.current = null; }
  };

  useEffect(() => {
    getDashboardStats()
      .then(res => {
        const data = res.data;
        setKpis({
          modelsCount: 50,
          providersCount: 3,
          checksCount: data.total_use_cases > 0 ? data.total_use_cases * 4 : 312,
          accuracy: data.recommendation_accuracy != null ? `${Math.round(data.recommendation_accuracy * 100)}%` : '91%',
        });
      })
      .catch(() => {});
    return () => clearStepTimer();
  }, []);

  const startStepTimer = () => {
    let step = 0;
    stepTimerRef.current = setInterval(() => {
      step++;
      if (step < 5) setCurrentStep(step);
      else clearStepTimer();
    }, 1200);
  };

  const handleSubmit = useCallback(async (description, structuredFields = {}) => {
    setFormState('loading');
    setCurrentStep(0);
    setError(null);
    setResult(null);
    setClarificationData(null);
    startStepTimer();

    try {
      const response = await submitUseCase(description, structuredFields);
      clearStepTimer();
      const data = response.data;

      if (data.status === 'needs_clarification') {
        setCurrentStep(0);
        setClarificationData(data);
        setFormState('clarifying');
        return;
      }

      setCurrentStep(5);
      await new Promise(r => setTimeout(r, 400));
      setResult(data);
      setFormState('complete');
      setChatMessages([{
        role: 'assistant',
        content: (
          `I've generated your full AI recommendation guidebook! Here's a quick summary:\n\n` +
          `**Recommended Model:** ${data.recommendation?.recommended_model || 'N/A'} by ${data.recommendation?.model_provider || 'N/A'}\n` +
          `**Cloud:** ${data.recommendation?.recommended_cloud || 'N/A'} · ${data.recommendation?.recommended_region || ''}\n` +
          `**Estimated Cost:** $${(data.recommendation?.estimated_monthly_cost || 0).toFixed(2)}/month\n\n` +
          `Browse the **6 tabs** in the recommendation panel for the full guidebook.\n\n` +
          `Ask me anything — costs, setup steps, compliance, why this model over another, how to reduce your bill...`
        ),
      }]);

    } catch (err) {
      clearStepTimer();
      console.error('Submission error:', err);
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
      setFormState('idle');
    }
  }, []);

  const handleSubmitClarification = async (answers) => {
    if (!clarificationData?.id) return;
    setFormState('loading');
    setCurrentStep(0);
    startStepTimer();

    try {
      const response = await submitClarification(clarificationData.id, answers);
      clearStepTimer();
      setCurrentStep(5);
      await new Promise(r => setTimeout(r, 400));
      const data = response.data;
      setResult(data);
      setFormState('complete');
      setChatMessages([{
        role: 'assistant',
        content: (
          `Thanks for the additional details! I've generated your complete recommendation guidebook.\n\n` +
          `**Model:** ${data.recommendation?.recommended_model || 'N/A'}\n` +
          `**Cloud:** ${data.recommendation?.recommended_cloud || 'N/A'} · ${data.recommendation?.recommended_region || ''}\n` +
          `**Cost:** $${(data.recommendation?.estimated_monthly_cost || 0).toFixed(2)}/month\n\n` +
          `Browse all 6 tabs for the full breakdown, or ask me anything!`
        ),
      }]);
    } catch (err) {
      clearStepTimer();
      console.error('Clarification error:', err);
      setError(err.response?.data?.detail || 'Something went wrong with clarification. Please try again.');
      setFormState('idle');
    }
  };

  const handleSkipClarification = () => {
    handleSubmitClarification({});
  };

  const handleReset = () => {
    window.history.replaceState({}, document.title);
    setFormState('idle');
    setResult(null);
    setCurrentStep(0);
    setError(null);
    setClarificationData(null);
    setChatMessages([]);
  };

  return (
    <div id="new-request-page" className="animate-fade-in space-y-6">

      {/* ── Hero section ── */}
      {formState === 'idle' && (
        <>
          <section className="hero">
            <div>
              <span className="hero-eyebrow"><Sparkles className="w-3 h-3" /> Recommendation engine v3</span>
              <h1>Find the right model and cloud for every use case</h1>
              <p>
                Describe your project in plain language — or fill in optional details for a more precise recommendation.
                The engine evaluates 50+ models and 3 cloud providers against cost, compliance, and performance.
              </p>
            </div>
          </section>

          <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10 }}>
            <StatsCard title="Models evaluated" value={kpis.modelsCount} icon={Cpu} iconBg="#1a1d2e" iconColor="#818cf8" />
            <StatsCard title="Cloud providers" value={kpis.providersCount} icon={Cloud} iconBg="#0e1c20" iconColor="#22d3ee" />
            <StatsCard title="Compliance checks" value={kpis.checksCount} icon={ShieldCheck} iconBg="#1a1009" iconColor="#f97316" />
            <StatsCard title="Avg accuracy" value={kpis.accuracy} icon={Target} iconBg="#0d1a0e" iconColor="#4ade80" />
          </section>
        </>
      )}

      {/* Error */}
      {error && (
        <div id="request-error" style={{ padding: '12px 16px', borderRadius: 10, background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.25)', color: '#f87171', fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* ── Form ── */}
      {formState === 'idle' && (
        <UseCaseForm 
          key={templateDescription ? 'template' : 'new'}
          onSubmit={handleSubmit} 
          isLoading={false} 
          initialDescription={templateDescription}
          initialStructuredFields={templateFields}
        />
      )}

      {/* ── Loading ── */}
      {formState === 'loading' && <LoadingSteps currentStep={currentStep} />}

      {/* ── Clarification ── */}
      {formState === 'clarifying' && clarificationData && (
        <div className="animate-fade-in">
          <ClarificationPanel
            data={clarificationData}
            onSubmit={handleSubmitClarification}
            onSkip={handleSkipClarification}
          />
        </div>
      )}

      {/* ── Complete: Chat + Guidebook ── */}
      {formState === 'complete' && result && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start animate-fade-in">
          {/* Chat */}
          <div className="lg:col-span-5" style={{ height: 640 }}>
            <ChatWidget
              useCaseId={result.id}
              initialMessages={chatMessages}
              onNewRequest={handleReset}
              onSwitchApplied={(updatedResult) => {
                setResult(updatedResult);
              }}
            />
          </div>

          {/* Guidebook */}
          <div className="lg:col-span-7">
            <RecommendationCard
              recommendation={result.recommendation}
              triage={result.triage}
              description={result.description}
            />
          </div>
        </div>
      )}
    </div>
  );
}
