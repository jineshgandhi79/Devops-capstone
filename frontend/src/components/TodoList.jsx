import TodoItem from './TodoItem'

const TITLES = {
  all: 'All tasks',
  active: 'Active tasks',
  today: 'Due today',
  overdue: 'Overdue',
  completed: 'Completed',
}

export default function TodoList({
  todos,
  loading,
  view,
  category,
  search,
  completedCount,
  colors,
  onToggle,
  onEdit,
  onDelete,
  onClearCompleted,
}) {
  const title = category || TITLES[view]

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>
          {title} <span className="pill">{todos.length}</span>
        </h2>
        {completedCount > 0 && (
          <button className="btn btn-ghost" onClick={onClearCompleted}>
            Clear completed ({completedCount})
          </button>
        )}
      </div>

      {loading ? (
        <ul className="todo-list" aria-busy="true">
          {[0, 1, 2].map((i) => (
            <li key={i} className="todo skeleton" />
          ))}
        </ul>
      ) : todos.length === 0 ? (
        <div className="empty">
          <div className="empty-icon" aria-hidden="true">
            ✓
          </div>
          <h3>{search ? 'No matching tasks' : 'Nothing here'}</h3>
          <p className="muted">
            {search
              ? `No tasks match “${search}”.`
              : view === 'completed'
                ? 'Completed tasks will show up here.'
                : 'Add a task above to get started.'}
          </p>
        </div>
      ) : (
        <ul className="todo-list">
          {todos.map((t) => (
            <TodoItem
              key={t.id}
              todo={t}
              color={colors[t.category]}
              onToggle={() => onToggle(t)}
              onEdit={() => onEdit(t)}
              onDelete={() => onDelete(t)}
            />
          ))}
        </ul>
      )}
    </section>
  )
}
