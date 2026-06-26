import { useState, useRef, useEffect } from 'react';
import { Bot, Send, ArrowRight } from 'lucide-react';
import { submitChat, switchRecommendation } from '../api/client';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Cell, PieChart, Pie,
} from 'recharts';

// ─── Inline Markdown helpers ──────────────────────────────────────────────────

function parseInlineMarkdown(text) {
  const boldCodeRegex = /(\*\*.*?\*\*|`.*?`)/g;
  const tokens = text.split(boldCodeRegex);
  return tokens.map((token, i) => {
    if (token.startsWith('**') && token.endsWith('**'))
      return <strong key={i} style={{ color: '#1E1B4B', fontWeight: 800 }}>{token.slice(2, -2)}</strong>;
    if (token.startsWith('`') && token.endsWith('`'))
      return <code key={i} style={{ background: '#F5F3FF', color: '#7C3AED', padding: '1px 6px', borderRadius: 4, fontSize: 11, fontFamily: 'monospace' }}>{token.slice(1, -1)}</code>;
    return token;
  });
}

// Exported for use in ClarificationPanel
export function formatMessageText(text) {
  if (!text) return '';
  const lines = text.split('\n');
  const renderedElements = [];
  let currentTable = null;

  const flushTable = (key) => {
    if (currentTable) {
      const tableEl = (
        <div key={key} style={{ overflowX: 'auto', margin: '12px 0', background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #E5E7EB', background: '#F5F3FF' }}>
                {currentTable.headers.map((h, i) => (
                  <th key={i} style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 'bold', color: '#1E1B4B' }}>
                    {parseInlineMarkdown(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {currentTable.rows.map((row, rowIndex) => (
                <tr key={rowIndex} style={{ borderBottom: rowIndex < currentTable.rows.length - 1 ? '1px solid #E5E7EB' : 'none' }}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} style={{ padding: '8px 10px', color: '#4B5563' }}>
                      {parseInlineMarkdown(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      renderedElements.push(tableEl);
      currentTable = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const parts = trimmed.split('|').map(p => p.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      const isSeparator = parts.every(p => p.match(/^:\s*-+\s*:?$|^-+\s*:?$|^:\s*-+$/));
      
      if (isSeparator) {
        continue;
      }
      
      if (!currentTable) {
        currentTable = { headers: parts, rows: [] };
      } else {
        currentTable.rows.push(parts);
      }
    } else {
      flushTable(`table-${i}`);
      
      if (line.startsWith('### ')) {
        renderedElements.push(<h4 key={i} style={{ color: '#1E1B4B', fontSize: 13, fontWeight: 700, margin: '12px 0 4px' }}>{line.slice(4)}</h4>);
      } else if (line.startsWith('## ')) {
        renderedElements.push(<h3 key={i} style={{ color: '#1E1B4B', fontSize: 14, fontWeight: 800, margin: '16px 0 6px' }}>{line.slice(3)}</h3>);
      } else if (line.startsWith('# ')) {
        renderedElements.push(<h2 key={i} style={{ color: '#1E1B4B', fontSize: 16, fontWeight: 800, margin: '18px 0 8px' }}>{line.slice(2)}</h2>);
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        renderedElements.push(
          <div key={i} style={{ display: 'flex', gap: 6, margin: '3px 0' }}>
            <span style={{ color: '#7C3AED', marginTop: 2 }}>•</span>
            <span style={{ color: '#4B5563', fontSize: 12, lineHeight: 1.6 }}>{parseInlineMarkdown(trimmed.slice(2))}</span>
          </div>
        );
      } else if (trimmed.match(/^\d+\. /)) {
        renderedElements.push(
          <div key={i} style={{ display: 'flex', gap: 6, margin: '3px 0' }}>
            <span style={{ color: '#7C3AED', fontSize: 11, minWidth: 16 }}>{trimmed.split('.')[0]}.</span>
            <span style={{ color: '#4B5563', fontSize: 12, lineHeight: 1.6 }}>{parseInlineMarkdown(trimmed.slice(trimmed.indexOf('.') + 2))}</span>
          </div>
        );
      } else if (trimmed) {
        renderedElements.push(<p key={i} style={{ color: '#4B5563', fontSize: 12, margin: '4px 0', lineHeight: 1.7 }}>{parseInlineMarkdown(line)}</p>);
      }
    }
  }
  
  flushTable('table-end');
  return renderedElements;
}

function ChatChart({ chart }) {
  if (!chart || !chart.data || !chart.data.length) return null;
  const colors = ['#C084FC', '#67E8F9', '#6EE7B7', '#FCA5A5', '#FDE68A'];
  return (
    <div style={{ marginTop: 12, background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 12, padding: '12px 14px', width: '100%', maxWidth: 340, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
      <p style={{ fontSize: 10, fontWeight: 700, color: '#7C3AED', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{chart.title}</p>
      <div style={{ height: 130 }}>
        <ResponsiveContainer width="100%" height="100%">
          {chart.type === 'pie' ? (
            <PieChart>
              <Pie data={chart.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={45} label={({ name }) => name.slice(0, 10)} labelLine={false}>
                {chart.data.map((_, index) => <Cell key={index} fill={colors[index % colors.length]} />)}
              </Pie>
              <Tooltip formatter={v => [`${v}`, 'Cost']} />
            </PieChart>
          ) : (
            <BarChart data={chart.data} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#9CA3AF' }} />
              <YAxis tick={{ fontSize: 9, fill: '#9CA3AF' }} />
              <Tooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={24}>
                {chart.data.map((_, index) => <Cell key={index} fill={colors[index % colors.length]} />)}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function ChatWidget({ useCaseId, initialMessages = [], onNewRequest, onSwitchApplied }) {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const handleApplySwitch = async (model, cloud) => {
    setLoading(true);
    try {
      const res = await switchRecommendation(useCaseId, model, cloud);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `🔄 **System**: Successfully switched recommendation to **${model || cloud}**. Regenerating guidebook...`
        }
      ]);
      if (onSwitchApplied) {
        onSwitchApplied(res.data);
      }
    } catch (err) {
      console.error('Failed to apply switch:', err);
      alert('Failed to switch recommendation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading || !useCaseId) return;
    const userText = input.trim();
    const updatedMessages = [...messages, { role: 'user', content: userText }];
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await submitChat(useCaseId, updatedMessages);
      setMessages([
        ...updatedMessages,
        {
          role: 'assistant',
          content: response.data.text,
          chart: response.data.chart,
          suggested_model: response.data.suggested_model,
          suggested_cloud: response.data.suggested_cloud
        },
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages([
        ...updatedMessages,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col chat-container" style={{ height: '100%', minHeight: 400 }}>
      {/* Chat header */}
      <div style={{ padding: '14px 18px', borderBottom: '1px solid #E5E7EB', background: '#F5F3FF', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTopLeftRadius: 16, borderTopRightRadius: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bot style={{ width: 18, height: 18, color: '#7C3AED' }} />
          <span style={{ fontWeight: 700, fontSize: 14, color: '#1E1B4B' }}>AI Advisor Chat</span>
          <span style={{ fontSize: 10, background: '#EDE9FE', color: '#7C3AED', padding: '2px 8px', borderRadius: 10, fontWeight: 600, border: '1px solid #C084FC' }}>Active Session</span>
        </div>
        {onNewRequest && (
          <button 
            onClick={onNewRequest} 
            style={{ fontSize: 12, fontWeight: 600, color: '#7C3AED', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            New Request <ArrowRight size={12} />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}>
            {msg.role === 'assistant' ? formatMessageText(msg.content) : msg.content}
            {msg.chart && <ChatChart chart={msg.chart} />}
            {msg.role === 'assistant' && (msg.suggested_model || msg.suggested_cloud) && (
              <div style={{ marginTop: 8 }}>
                <button
                  onClick={() => handleApplySwitch(msg.suggested_model, msg.suggested_cloud)}
                  disabled={loading}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 8,
                    background: '#F5F3FF',
                    border: '1px solid #C084FC',
                    color: '#7C3AED',
                    fontSize: 11,
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = '#EDE9FE';
                    e.currentTarget.style.borderColor = '#7C3AED';
                    e.currentTarget.style.color = '#5B21B6';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = '#F5F3FF';
                    e.currentTarget.style.borderColor = '#C084FC';
                    e.currentTarget.style.color = '#7C3AED';
                  }}
                >
                  Apply Switch to {msg.suggested_model ? `model: ${msg.suggested_model}` : `cloud: ${msg.suggested_cloud}`}
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '10px 14px' }}>
            {[0, 0.2, 0.4].map((delay, i) => (
              <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#C084FC', display: 'inline-block', animation: `bounce 1s ${delay}s infinite` }} />
            ))}
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-area border-t p-3 flex gap-2" style={{ borderColor: '#E5E7EB', background: '#F5F3FF', borderBottomLeftRadius: 16, borderBottomRightRadius: 16 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about cost, setup steps, model comparisons..."
          className="chat-input-field flex-1"
          style={{ background: '#FFFFFF', border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 14px', color: '#1E1B4B', fontSize: 14, outline: 'none' }}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="btn-primary"
          style={{ padding: '10px 18px', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: 'pointer', background: 'linear-gradient(135deg, #7C3AED, #6366F1)', color: '#fff', border: 'none', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Send style={{ width: 14, height: 14 }} />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
}
