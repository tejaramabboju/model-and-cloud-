import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Sparkles, SquarePlus as PlusSquare, ChartBar as BarChart3, History, ChevronLeft, ChevronRight } from 'lucide-react';

const navItems = [
  { to: '/', icon: PlusSquare, label: 'New request', id: 'nav-new-request' },
  { to: '/history', icon: History, label: 'History', id: 'nav-history' },
  { to: '/dashboard', icon: BarChart3, label: 'Dashboard', id: 'nav-dashboard' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside id="sidebar" className={collapsed ? 'collapsed' : ''}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start', marginBottom: 28, gap: 10 }}>
        {collapsed ? (
          <button
            id="sidebar-toggle-expand"
            onClick={() => setCollapsed(false)}
            style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #C084FC, #67E8F9)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: 'none', color: '#fff', cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(192, 132, 252, 0.3)',
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
            <div className="mark">
              <Sparkles style={{ width: 18, height: 18, color: '#fff' }} />
            </div>

            <div className="sidebar-text">
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1E1B4B', lineHeight: 1.2 }}>AI Advisor</div>
              <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 2 }}>Model &amp; Cloud Engine</div>
            </div>

            <button
              id="sidebar-toggle-collapse"
              onClick={() => setCollapsed(true)}
              className="sidebar-toggle"
              style={{ marginLeft: 'auto' }}
              title="Collapse sidebar"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft style={{ width: 14, height: 14 }} />
            </button>
          </>
        )}
      </div>

      {/* Navigation */}
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
                <Icon style={{ width: 18, height: 18, flexShrink: 0 }} />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div id="sidebar-footer">
        <span className="sidebar-footer-text" style={{ fontSize: 10, color: '#9CA3AF' }}>AI Advisor</span>
        <span className="sidebar-footer-text" style={{ fontSize: 10, color: '#9CA3AF', fontFamily: 'JetBrains Mono, monospace' }}>v3.0.0</span>
      </div>
    </aside>
  );
}
