import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/', icon: '💬', label: 'Chat' },
  { path: '/analytics', icon: '📊', label: 'Analytics' },
  { path: '/memory', icon: '🧠', label: 'Memory' },
  { path: '/persona', icon: '💜', label: 'Persona' },
  { path: '/settings', icon: '⚙️', label: 'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">FENRY</div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-btn ${isActive ? 'active' : ''}`}
          >
            {item.icon}
            <span className="tooltip">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
