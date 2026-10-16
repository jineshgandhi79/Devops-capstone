import { useState } from 'react'
import { greeting } from '../utils/dates'

function todayLabel() {
  return new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })
}

export default function Header({ search, onSearch, sort, onSort }) {
  // Computed once on mount so re-renders stay pure
  const [{ hello, today }] = useState(() => ({ hello: greeting(), today: todayLabel() }))

  return (
    <header className="header">
      <div>
        <h1>{hello}, Jinesh</h1>
        <p className="muted">{today}</p>
      </div>

      <div className="header-controls">
        <label className="search">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            placeholder="Search tasks…"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            aria-label="Search tasks"
          />
        </label>
        <select value={sort} onChange={(e) => onSort(e.target.value)} aria-label="Sort tasks">
          <option value="created">Newest first</option>
          <option value="due_date">Due date</option>
          <option value="priority">Priority</option>
          <option value="title">Title A–Z</option>
        </select>
      </div>
    </header>
  )
}
