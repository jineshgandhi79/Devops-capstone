import { useEffect, useState } from 'react'

export default function TodoModal({ todo, categories, onClose, onSave }) {
  const [form, setForm] = useState({
    title: todo.title,
    description: todo.description ?? '',
    priority: todo.priority,
    category: todo.category,
    due_date: todo.due_date ?? '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave({
        title: form.title.trim(),
        description: form.description.trim() || null,
        priority: form.priority,
        category: form.category.trim() || 'General',
        due_date: form.due_date || null,
      })
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-label="Edit task">
        <div className="modal-head">
          <h2>Edit task</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {error && <div className="banner banner-error">{error}</div>}

        <label className="field">
          <span>Title</span>
          <input value={form.title} onChange={set('title')} maxLength={200} required autoFocus />
        </label>

        <label className="field">
          <span>Notes</span>
          <textarea
            rows={3}
            value={form.description}
            onChange={set('description')}
            maxLength={2000}
            placeholder="Add details…"
          />
        </label>

        <div className="field-row">
          <label className="field">
            <span>Priority</span>
            <select value={form.priority} onChange={set('priority')}>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </label>
          <label className="field">
            <span>Category</span>
            <input list="modal-categories" value={form.category} onChange={set('category')} maxLength={50} />
            <datalist id="modal-categories">
              {categories.map((c) => (
                <option key={c} value={c} />
              ))}
            </datalist>
          </label>
          <label className="field">
            <span>Due date</span>
            <input type="date" value={form.due_date} onChange={set('due_date')} />
          </label>
        </div>

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" disabled={!form.title.trim() || saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>
    </div>
  )
}
