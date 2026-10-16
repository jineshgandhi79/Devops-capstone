export default function StatCards({ stats }) {
  const cards = [
    { label: 'Total tasks', value: stats.total, tone: 'indigo' },
    { label: 'Active', value: stats.active, tone: 'sky' },
    { label: 'Completed', value: stats.completed, tone: 'green' },
    { label: 'Overdue', value: stats.overdue, tone: 'red' },
  ]

  return (
    <section className="stats" aria-label="Summary">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card tone-${c.tone}`}>
          <div className="stat-label">{c.label}</div>
          <div className="stat-value">{c.value}</div>
        </div>
      ))}

      <div className="stat-card progress-card">
        <div className="progress-head">
          <span className="stat-label">Progress</span>
          <strong>{stats.completion_rate}%</strong>
        </div>
        <div
          className="progress-track"
          role="progressbar"
          aria-valuenow={stats.completion_rate}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="progress-fill" style={{ width: `${stats.completion_rate}%` }} />
        </div>
        <div className="priority-split">
          <span>
            <i className="dot dot-high" /> {stats.by_priority.HIGH ?? 0} high
          </span>
          <span>
            <i className="dot dot-medium" /> {stats.by_priority.MEDIUM ?? 0} medium
          </span>
          <span>
            <i className="dot dot-low" /> {stats.by_priority.LOW ?? 0} low
          </span>
        </div>
      </div>
    </section>
  )
}
