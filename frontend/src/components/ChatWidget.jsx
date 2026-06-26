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
      return <strong key={i} style={{ color: '#e2e8f0', fontWeight: 800 }}>{token.slice(2, -2)}</strong>;
    if (token.startsWith('`') && token.endsWith('`'))
      return <code key={i} style={{ background: '#1e2535', color: '#818cf8', padding: '1px 6px', borderRadius: 4, fontSize: 11, fontFamily: 'monospace' }}>{token.slice(1, -1)}</code>;
    return token;
  });
}

export function formatMessageText(text) {
  if (!text) return '';
  const lines = text.split('\n');
  const renderedElements = [];
  let currentTable = null;

  const flushTable = (key) => {
    if (currentTable) {
      const tableEl = (
        <div key={key} style={{ overflowX: 'auto', margin: '12px 0', background: '#0d1117', border: '1px solid #1e2535', borderRadius: 8 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e2535', background: '#161b22' }}>
                {currentTable.headers.map((h, i) => (
                  <th key={i} style={{ padding: '8px 10px', textAlign: 'left', fontWeight: 'bold', color: '#cbd5e1' }}>
                    {parseInlineMarkdown(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {currentTable.rows.map((row, rowIndex) => (
                <tr key={rowIndex} style={{ borderBottom: rowIndex < currentTable.rows.length - 1 ? '1px solid #1e2535' : 'none' }}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} style={{ padding: '8px 10px', color: '#8892b0' }}>
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
        renderedElements.push(<h4 key={i} style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 700, margin: '12px 0 4px' }}>{line.slice(4)}</h4>);
      } else if (line.startsWith('## ')) {
        renderedElements.push(<h3 key={i} style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 800, margin: '16px 0 6px' }}>{line.slice(3)}</h3>);
      } else if (line.startsWith('# ')) {
        renderedElements.push(<h2 key={i} style={{ color: '#f1f5f9', fontSize: 16, fontWeight: 800, margin: '18px 0 8px' }}>{line.slice(2)}</h2>);
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        renderedElements.push(
          <div key={i} style={{ display: 'flex', gap: 6, margin: '3px 0' }}>
            <span style={{ color: '#6366f1', marginTop: 2 }}>•</span>
            <span style={{ color: '#8892b0', fontSize: 12, lineHeight: 1.6 }}>{parseInlineMarkdown(trimmed.slice(2))}</span>
          </div>
        );
      } else if (trimmed.match(/^\d+\. /)) {
        renderedElements.push(
          <div key={i} style={{ display: 'flex', gap: 6, margin: '3px 0' }}>
            <span style={{ color: '#6366f1', fontSize: 11, minWidth: 16 }}>{trimmed.split('.')[0]}.</span>
            <span style={{ color: '#8892b0', fontSize: 12, lineHeight: 1.6 }}>{parseInlineMarkdown(trimmed.slice(trimmed.indexOf('.') + 2))}</span>
          </div>
        );
      } else if (trimmed) {
        renderedElements.push(<p key={i} style={{ color: '#8892b0', fontSize: 12, margin: '4px 0', lineHeight: 1.7 }}>{parseInlineMarkdown(line)}</p>);
      }
    }
  }
  
  flushTable('table-end');
  return renderedElements;
}

function ChatChart({ chart }) {
  if (!chart || !chart.data || !chart.data.length) return null;
  const colors = ['#6366F1', '#8B5CF6', '#22D3EE', '#D85A30', '#4ade80'];
  return (
    <div style={{ marginTop: 12, background: '#0d0f1a', border: '1px solid #1e2535', borderRadius: 10, padding: '12px 14px', width: '100%', maxWidth: 340 }}>
      <p style={{ fontSize: 10, fontWeight: 700, color: '#818cf8', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{chart.title}</p>
      <div style={{ height: 130 }}>
        <ResponsiveContainer width="100%" height="100%">
          {chart.type === 'pie' ? (
            <PieChart>
              <Pie data={chart.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={45} label={({ name }) => name.slice(0, 10)} labelLine={false}>
                {chart.data.map((_, index) => <Cell key={index} fill={colors[index % colors.length]} />)}
              </Pie>
              <Tooltip formatter={v => [`$${v}`, 'Cost']} />
            </PieChart>
          ) : (
            <BarChart data={chart.data} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2535" />
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748B' }} />
              <YAxis tick={{ fontSize: 9, fill: '#64748B' }} />
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
      <div style={{ padding: '14px 18px', borderBottom: '1px solid #1e2535', background: '#0d0f1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTopLeftRadius: 12, borderTopRightRadius: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bot style={{ width: 16, height: 16, color: '#818cf8' }} />
          <span style={{ fontWeight: 700, fontSize: 13, color: '#e2e8f0' }}>AI Advisor Chat</span>
          <span style={{ fontSize: 10, background: 'rgba(99,102,241,0.15)', color: '#818cf8', padding: '2px 7px', borderRadius: 10, fontWeight: 600 }}>Active Session</span>
        </div>
        {onNewRequest && (
          <button 
            onClick={onNewRequest} 
            style={{ fontSize: 11, fontWeight: 600, color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            New Request <ArrowRight size={10} />
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
                    borderRadius: 6,
                    background: 'rgba(99, 102, 241, 0.15)',
                    border: '1px solid rgba(99, 102, 241, 0.3)',
                    color: '#a5b4fc',
                    fontSize: 11,
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(99, 102, 241, 0.25)';
                    e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.5)';
                    e.currentTarget.style.color = '#fff';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(99, 102, 241, 0.15)';
                    e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.3)';
                    e.currentTarget.style.color = '#a5b4fc';
                  }}
                >
                  🔄 Apply Switch to {msg.suggested_model ? `model: ${msg.suggested_model}` : `cloud: ${msg.suggested_cloud}`}
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '10px 14px' }}>
            {[0, 0.2, 0.4].map((delay, i) => (
              <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#5c6189', display: 'inline-block', animation: `bounce 1s ${delay}s infinite` }} />
            ))}
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-area border-t p-3 flex gap-2" style={{ borderColor: '#1e2535', background: '#0d0f1a', borderBottomLeftRadius: 12, borderBottomRightRadius: 12 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about cost, setup steps, model comparisons..."
          className="chat-input-field flex-1"
          style={{ background: '#07090e', border: '1px solid #1e2535', borderRadius: 8, padding: '8px 12px', color: '#c9d1e8', fontSize: 13, outline: 'none' }}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="btn-primary"
          style={{ padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', color: '#fff', border: 'none', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Send style={{ width: 12, height: 12 }} />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
}
