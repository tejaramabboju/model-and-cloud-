import { useState, useEffect } from 'react';
import { Key, CircleCheck as CheckCircle2, Shield, Circle as HelpCircle, HardDrive } from 'lucide-react';
import axios from 'axios';

export default function Settings() {
  const [dbStatus, setDbStatus] = useState('Checking...');
  const [stats, setStats] = useState({ total_use_cases: 0 });

  useEffect(() => {
    axios.get('/api/dashboard-stats')
      .then(res => {
        setStats(res.data);
        setDbStatus('Connected (SQLite)');
      })
      .catch(() => {
        setDbStatus('Error connecting to DB');
      });
  }, []);

  return (
    <div id="settings-page" className="animate-fade-in space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">System Settings</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* API Credentials */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
              <Key className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">API Credentials</h2>
              <p className="text-xs text-gray-500">Manage LLM keys loaded from backend environment.</p>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div>
              <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1.5">
                Google Gemini API Key
              </label>
              <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5">
                <span className="text-xs font-mono text-gray-400 truncate">••••••••••••••••••••••••••••••••</span>
                <span className="ml-auto badge badge-emerald">
                  <CheckCircle2 className="w-3 h-3" />
                  Loaded
                </span>
              </div>
            </div>

            <div className="text-xs text-gray-500 leading-relaxed flex gap-1.5 items-start mt-2">
              <HelpCircle className="w-3.5 h-3.5 mt-0.5 text-gray-400 flex-shrink-0" />
              <span>To change the API key, update the <code>GEMINI_API_KEY</code> variable inside the <code>backend/.env</code> file on your local system and restart the server.</span>
            </div>
          </div>
        </div>

        {/* System & Diagnostics */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-100 flex items-center justify-center">
              <HardDrive className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">System Diagnostics</h2>
              <p className="text-xs text-gray-500">Monitor active database and server resources.</p>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Database Status</span>
              <span className="text-xs font-medium text-gray-900">{dbStatus}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Total Use Cases</span>
              <span className="text-xs font-mono font-mono-numbers text-gray-900">{stats.total_use_cases}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Target Model Registry</span>
              <span className="text-xs font-medium text-purple-700">gemini-2.5-flash</span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-500">Compliance Engine</span>
              <span className="badge badge-blue">HIPAA / GDPR / SOC2</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
