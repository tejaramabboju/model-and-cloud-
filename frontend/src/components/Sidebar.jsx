import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Sparkles, PlusSquare, BarChart3, History, ChevronLeft, ChevronRight } from 'lucide-react';

const navItems = [
  { to: '/', icon: PlusSquare, label: 'New request', id: 'nav-new-request' },
  { to: '/history', icon: History, label: 'History', id: 'nav-history' },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard', id: 'nav-dashboard' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside id="sidebar" className={collapsed ? 'collapsed' : ''}>

      {/* ── Top section: brand + toggle ─────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start', marginBottom: 28, gap: 10 }}>
        {/* Logo mark or Expand/Collapse Toggle */}
        {collapsed ? (
          <button
            id="sidebar-toggle-expand"
            onClick={() => setCollapsed(false)}
            style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg,#6366F1,#8B5CF6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: 'none', color: '#fff', cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(99,102,241,0.3)',
              transition: 'transform 0.15s ease',
              flexShrink: 0,
            }}
            title="Expand sidebar"
            aria-label="Expand sidebar"
            onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.08)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
          >
            <ChevronRight style={{ width: 18, height: 18 }} />
          </button>
        ) : (
          <>
            <div
              className="mark"
              style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'linear-gradient(135deg,#6366F1,#8B5CF6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <Sparkles style={{ width: 17, height: 17, color: '#fff' }} />
            </div>

            <div className="sidebar-text">
              <div style={{ fontSize: 13, fontWeight: 500, color: '#fff', lineHeight: 1.2 }}>AI Advisor</div>
              <div style={{ fontSize: 10, color: '#4b5280', marginTop: 2 }}>Model &amp; Cloud Engine</div>
            </div>

            <button
              id="sidebar-toggle-collapse"
              onClick={() => setCollapsed(true)}
              style={{
                marginLeft: 'auto', flexShrink: 0,
                width: 24, height: 24, borderRadius: 6,
                background: 'transparent', border: '0.5px solid #2a2d3a',
                color: '#5c6189', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'background 0.15s ease, color 0.15s ease',
              }}
              title="Collapse sidebar"
              aria-label="Collapse sidebar"
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; e.currentTarget.style.color = '#e2e8f0'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#5c6189'; }}
            >
              <ChevronLeft style={{ width: 14, height: 14 }} />
            </button>
          </>
        )}
      </div>

      {/* ── Navigation ───────────────────────────────────── */}
      <nav id="sidebar-nav" style={{ flex: 1 }}>
        <p className="nav-section-label">Workspace</p>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {navItems.map(({ to, icon: Icon, label, id }) => (
            <li key={to}>
              <NavLink
                id={id}
                to={to}
                end={to === '/'}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                title={label}
              >
                <Icon style={{ width: 16, height: 16, flexShrink: 0 }} />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* ── Footer ───────────────────────────────────────── */}
      <div id="sidebar-footer">
        <span className="sidebar-footer-text" style={{ fontSize: 10, color: '#3d4260' }}>AI Advisor</span>
        <span className="sidebar-footer-text" style={{ fontSize: 10, color: '#3d4260', fontFamily: 'JetBrains Mono, monospace' }}>v2.0.0</span>
      </div>
    </aside>
  );
}
