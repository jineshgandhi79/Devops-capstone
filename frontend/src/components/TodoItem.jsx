import { useEffect, useState } from 'react'
import { describeDueDate } from '../utils/dates'

export default function TodoItem({ todo, color, onToggle, onEdit, onDelete }) {
  const [confirming, setConfirming] = useState(false)
  const due = describeDueDate(todo.due_date, todo.completed)

  // Reset the "Confirm?" state if the user doesn't follow through
  useEffect(() => {
    if (!confirming) return
    const timer = setTimeout(() => setConfirming(false), 3000)
    return () => clearTimeout(timer)
  }, [confirming])

  return (
    <li className={`todo ${todo.completed ? 'done' : ''} priority-${todo.priority.toLowerCase()}`}>
      <button
        className="check"
        onClick={onToggle}
        aria-label={todo.completed ? `Mark "${todo.title}" as active` : `Complete "${todo.title}"`}
        aria-pressed={todo.completed}
      >
        {todo.completed ? '✓' : ''}
      </button>

      <div className="todo-body" onDoubleClick={onEdit}>
        <div className="todo-title">{todo.title}</div>
        {todo.description && <div className="todo-desc">{todo.description}</div>}
        <div className="todo-meta">
          <span className="chip">
            <i className="dot" style={{ background: color ?? '#9ca0b5' }} />
            {todo.category}
          </span>
          <span className={`badge badge-${todo.priority.toLowerCase()}`}>{todo.priority}</span>
          {due && <span className={`due due-${due.tone}`}>{due.label}</span>}
        </div>
      </div>

      <div className="todo-actions">
        <button className="icon-btn" onClick={onEdit} aria-label={`Edit "${todo.title}"`}>
          ✎
        </button>
        {confirming ? (
          <button className="btn btn-danger btn-sm" onClick={onDelete}>
            Delete?
          </button>
        ) : (
          <button
            className="icon-btn"
            onClick={() => setConfirming(true)}
            aria-label={`Delete "${todo.title}"`}
          >
            🗑
          </button>
        )}
      </div>
    </li>
  )
}
