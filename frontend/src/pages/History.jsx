import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History as HistoryIcon, Loader2 } from 'lucide-react';
import HistoryTable from '../components/HistoryTable';
import RecommendationCard from '../components/RecommendationCard';
import ChatWidget from '../components/ChatWidget';
import { getUseCases } from '../api/client';

const slideOverStyles = `
@keyframes slideLeft {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
`;

export default function History() {
  const navigate = useNavigate();
  const [useCases, setUseCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUseCase, setSelectedUseCase] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      try {
        const res = await getUseCases();
        if (!cancelled) setUseCases(res.data);
      } catch (err) {
        if (!cancelled) setError('Failed to load history.');
        console.error(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();
    return () => { cancelled = true; };
  }, []);

  return (
    <div id="history-page" className="animate-fade-in">
      <style>{slideOverStyles}</style>

      {/* Page Header */}
      <div className="mb-6">
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="glass-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <Loader2 style={{ width: 32, height: 32, color: '#22D3EE', margin: '0 auto 16px', animation: 'spin 1s linear infinite' }} />
          <p style={{ fontSize: 13, color: '#5c6189' }}>Loading history...</p>
        </div>
      )}

      {/* Table */}
      {!loading && <HistoryTable useCases={useCases} onSelectUseCase={setSelectedUseCase} />}

      {/* Slide-over Panel */}
      {selectedUseCase && (
        <div 
          style={{ 
            position: 'fixed', 
            top: 0, 
            right: 0, 
            bottom: 0, 
            left: 0, 
            zIndex: 100, 
            display: 'flex', 
            justifyContent: 'flex-end', 
            background: 'rgba(5, 8, 16, 0.7)', 
            backdropFilter: 'blur(8px)',
            animation: 'fadeIn 0.25s ease-out'
          }}
          onClick={() => setSelectedUseCase(null)}
        >
          <div 
            style={{ 
              width: '100%', 
              maxWidth: '900px', 
              background: '#080c14', 
              borderLeft: '1px solid #1e2535', 
              boxShadow: '-10px 0 30px rgba(0,0,0,0.5)',
              display: 'flex', 
              flexDirection: 'column',
              animation: 'slideLeft 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              height: '100%'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ padding: '16px 24px', borderBottom: '1px solid #1e2535', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0d1117' }}>
              <div>
                <h2 style={{ fontSize: 15, fontWeight: 800, color: '#f1f5f9', margin: 0 }}>Advisory Guidebook & Chat</h2>
                <p style={{ fontSize: 11, color: '#64748b', margin: '2px 0 0' }}>Created on {new Date(selectedUseCase.created_at).toLocaleDateString()}</p>
              </div>
              <button 
                onClick={() => setSelectedUseCase(null)}
                style={{ background: 'none', border: 'none', color: '#64748b', fontSize: 20, cursor: 'pointer', fontWeight: 300 }}
              >
                ✕
              </button>
            </div>

            {/* Content: Two-column layout */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 0, overflow: 'hidden' }}>
              {/* Left Column: Reusable ChatWidget */}
              <div style={{ borderRight: '1px solid #1e2535', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <ChatWidget 
                  useCaseId={selectedUseCase.id} 
                  initialMessages={[]} 
                  onNewRequest={() => {
                    setSelectedUseCase(null);
                    navigate('/');
                  }}
                  onSwitchApplied={(updatedResult) => {
                    setSelectedUseCase(updatedResult);
                    setUseCases(prev => prev.map(uc => uc.id === updatedResult.id ? updatedResult : uc));
                  }}
                />
              </div>

              {/* Right Column: RecommendationCard + Original Request summary */}
              <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <h3 style={{ fontSize: 10, fontWeight: 700, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>Original Request</h3>
                    <button 
                      onClick={() => {
                        const description = selectedUseCase.description;
                        const fields = selectedUseCase.extracted_fields || {};
                        setSelectedUseCase(null);
                        navigate('/', { state: { templateDescription: description, templateFields: fields } });
                      }}
                      style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', color: '#818cf8', borderRadius: 4, padding: '3px 8px', fontSize: 10.5, fontWeight: 700, cursor: 'pointer', transition: 'all 0.15s' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.2)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'rgba(99,102,241,0.12)'}
                    >
                      Use as Template
                    </button>
                  </div>
                  <div style={{ background: '#0A0C12', border: '1px solid #1e2535', borderRadius: 8, padding: '10px 14px', fontSize: 12.5, color: '#94a3b8', lineHeight: 1.6 }}>
                    {selectedUseCase.description}
                  </div>
                </div>

                <RecommendationCard 
                  recommendation={selectedUseCase.recommendation} 
                  triage={selectedUseCase.triage} 
                  description={selectedUseCase.description} 
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
