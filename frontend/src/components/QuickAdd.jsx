import { useState } from 'react'

export default function QuickAdd({ categories, defaultCategory, onAdd }) {
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('MEDIUM')
  const [category, setCategory] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    await onAdd({
      title: title.trim(),
      priority,
      category: category.trim() || defaultCategory || 'General',
      due_date: dueDate || null,
    })
    setSaving(false)
    setTitle('')
    setDueDate('')
  }

  return (
    <form className="quick-add" onSubmit={submit}>
      <input
        className="quick-title"
        placeholder="Add a new task…"
        value={title}
        maxLength={200}
        onChange={(e) => setTitle(e.target.value)}
        aria-label="Task title"
      />
      <div className="quick-options">
        <select value={priority} onChange={(e) => setPriority(e.target.value)} aria-label="Priority">
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <input
          list="category-options"
          placeholder={defaultCategory || 'Category'}
          value={category}
          maxLength={50}
          onChange={(e) => setCategory(e.target.value)}
          aria-label="Category"
        />
        <datalist id="category-options">
          {categories.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          aria-label="Due date"
        />
        <button className="btn btn-primary" disabled={!title.trim() || saving}>
          {saving ? 'Adding…' : 'Add task'}
        </button>
      </div>
    </form>
  )
}
