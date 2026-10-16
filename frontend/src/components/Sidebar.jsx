const VIEWS = [
  { key: 'all', label: 'All tasks', icon: '☰', count: (s) => s.total },
  { key: 'active', label: 'Active', icon: '○', count: (s) => s.active },
  { key: 'today', label: 'Due today', icon: '◷', count: (s) => s.due_today },
  { key: 'overdue', label: 'Overdue', icon: '!', count: (s) => s.overdue },
  { key: 'completed', label: 'Completed', icon: '✓', count: (s) => s.completed },
]

export default function Sidebar({ view, onViewChange, category, onCategoryChange, stats, info, colors }) {
  const categories = Object.entries(stats.by_category)

  return (
    <aside className="sidebar">
      <div className="sidebar-inner">
        <div className="brand">
          <div className="brand-logo" aria-hidden="true">
            ✓
          </div>
          <div>
            <div className="brand-name">DevTrack Todo</div>
            <div className="brand-sub">Stay on top of your work</div>
          </div>
        </div>
  
        <nav className="nav" aria-label="Views">
          <div className="nav-heading">Views</div>
          {VIEWS.map((v) => (
            <button
              key={v.key}
              className={`nav-item ${!category && view === v.key ? 'active' : ''} ${
                v.key === 'overdue' && stats.overdue > 0 ? 'nav-alert' : ''
              }`}
              onClick={() => onViewChange(v.key)}
            >
              <span className="nav-icon" aria-hidden="true">
                {v.icon}
              </span>
              <span className="nav-label">{v.label}</span>
              <span className="nav-count">{v.count(stats)}</span>
            </button>
          ))}
        </nav>
  
        {categories.length > 0 && (
          <nav className="nav" aria-label="Categories">
            <div className="nav-heading">Categories</div>
            {categories.map(([name, count]) => (
              <button
                key={name}
                className={`nav-item ${category === name ? 'active' : ''}`}
                onClick={() => onCategoryChange(category === name ? '' : name)}
              >
                <span className="nav-dot" style={{ background: colors[name] }} />
                <span className="nav-label">{name}</span>
                <span className="nav-count">{count}</span>
              </button>
            ))}
          </nav>
        )}
  
        <div className="sidebar-footer">
          <div className="pipeline">
            <span className="pipeline-dot" />
            {info ? `v${info.version} · ${info.environment}` : 'API offline'}
          </div>
          <div className="author">
            Built by <strong>Jinesh Gandhi</strong>
          </div>
        </div>
      </div>
    </aside>
  )
}

const PALETTE = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#ef4444']

// Colour by position in the (alphabetical) category list so the first eight never collide
export function categoryColors(categories) {
  return Object.fromEntries(categories.map((name, i) => [name, PALETTE[i % PALETTE.length]]))
}
