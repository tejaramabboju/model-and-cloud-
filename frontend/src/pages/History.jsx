import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History as HistoryIcon, Loader as Loader2 } from 'lucide-react';
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

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="glass-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <Loader2 style={{ width: 32, height: 32, color: '#C084FC', margin: '0 auto 16px', animation: 'spin 1s linear infinite' }} />
          <p style={{ fontSize: 14, color: '#6B7280' }}>Loading history...</p>
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
            background: 'rgba(30, 27, 75, 0.3)', 
            backdropFilter: 'blur(8px)',
            animation: 'fadeIn 0.25s ease-out'
          }}
          onClick={() => setSelectedUseCase(null)}
        >
          <div 
            style={{ 
              width: '100%', 
              maxWidth: '900px', 
              background: '#FFFFFF', 
              borderLeft: '1px solid #E5E7EB', 
              boxShadow: '-10px 0 30px rgba(0,0,0,0.1)',
              display: 'flex', 
              flexDirection: 'column',
              animation: 'slideLeft 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              height: '100%'
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ padding: '16px 24px', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F5F3FF' }}>
              <div>
                <h2 style={{ fontSize: 16, fontWeight: 800, color: '#1E1B4B', margin: 0 }}>Advisory Guidebook & Chat</h2>
                <p style={{ fontSize: 12, color: '#6B7280', margin: '2px 0 0' }}>Created on {new Date(selectedUseCase.created_at).toLocaleDateString()}</p>
              </div>
              <button 
                onClick={() => setSelectedUseCase(null)}
                style={{ background: 'none', border: 'none', color: '#6B7280', fontSize: 20, cursor: 'pointer', fontWeight: 300, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8, transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#F3F4F6'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                ✕
              </button>
            </div>

            {/* Content: Two-column layout */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 0, overflow: 'hidden' }}>
              {/* Left Column: Chat */}
              <div style={{ borderRight: '1px solid #E5E7EB', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
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

              {/* Right Column: RecommendationCard + Original Request */}
              <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <h3 style={{ fontSize: 11, fontWeight: 700, color: '#7C3AED', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>Original Request</h3>
                    <button 
                      onClick={() => {
                        const description = selectedUseCase.description;
                        const fields = selectedUseCase.extracted_fields || {};
                        setSelectedUseCase(null);
                        navigate('/', { state: { templateDescription: description, templateFields: fields } });
                      }}
                      style={{ background: '#F5F3FF', border: '1px solid #C084FC', color: '#7C3AED', borderRadius: 8, padding: '4px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer', transition: 'all 0.15s' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#EDE9FE'}
                      onMouseLeave={e => e.currentTarget.style.background = '#F5F3FF'}
                    >
                      Use as Template
                    </button>
                  </div>
                  <div style={{ background: '#FAFAFA', border: '1px solid #E5E7EB', borderRadius: 10, padding: '12px 16px', fontSize: 13, color: '#4B5563', lineHeight: 1.6 }}>
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
