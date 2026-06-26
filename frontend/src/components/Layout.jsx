import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

const pageMeta = {
  '/': { title: 'New request', badge: 'Gemini powered' },
  '/history': { title: 'History', badge: null },
  '/dashboard': { title: 'Dashboard', badge: null },
};

function getMonthYear() {
  return new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

export default function Layout() {
  const location = useLocation();
  const meta = pageMeta[location.pathname] ?? { title: 'AI Advisor', badge: null };

  return (
    <div
      id="layout-root"
      style={{ display: 'flex', minHeight: '100vh', background: '#F8F7FF', color: '#4B5563' }}
    >
      <Sidebar />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh', overflow: 'hidden' }}>
        <div className="topbar">
          <span className="page-title">{meta.title}</span>
          {meta.badge ? (
            <span className="badge-ai">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              {meta.badge}
            </span>
          ) : location.pathname === '/dashboard' ? (
            <span className="date-chip">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {getMonthYear()}
            </span>
          ) : null}
        </div>

        <main style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
