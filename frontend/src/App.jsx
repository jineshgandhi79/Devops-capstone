import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import Sidebar, { categoryColors } from './components/Sidebar'
import Header from './components/Header'
import StatCards from './components/StatCards'
import QuickAdd from './components/QuickAdd'
import TodoList from './components/TodoList'
import TodoModal from './components/TodoModal'

const EMPTY_STATS = {
  total: 0,
  active: 0,
  completed: 0,
  overdue: 0,
  due_today: 0,
  completion_rate: 0,
  by_priority: { HIGH: 0, MEDIUM: 0, LOW: 0 },
  by_category: {},
}

export default function App() {
  const [todos, setTodos] = useState([])
  const [stats, setStats] = useState(EMPTY_STATS)
  const [info, setInfo] = useState(null)
  const [view, setView] = useState('all')
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('created')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)

  const refresh = useCallback(async () => {
    const params = { status: view, sort }
    if (category) params.category = category
    if (search.trim()) params.search = search.trim()
    try {
      const [list, summary] = await Promise.all([api.listTodos(params), api.stats()])
      setTodos(list)
      setStats(summary)
      setError('')
    } catch (err) {
      setError(`Could not reach the API (${err.message}). Is the backend running?`)
    } finally {
      setLoading(false)
    }
  }, [view, category, search, sort])

  // Debounce so typing in the search box doesn't fire a request per keystroke
  useEffect(() => {
    const timer = setTimeout(refresh, search ? 250 : 0)
    return () => clearTimeout(timer)
  }, [refresh, search])

  useEffect(() => {
    api.info().then(setInfo).catch(() => setInfo(null))
  }, [])

  // Run a mutation, then reload; surface failures in the banner
  const mutate = async (action) => {
    try {
      await action()
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  const categories = Object.keys(stats.by_category)
  const colors = categoryColors(categories)

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        onViewChange={(v) => {
          setView(v)
          setCategory('')
        }}
        category={category}
        onCategoryChange={(c) => {
          setCategory(c)
          setView('all')
        }}
        stats={stats}
        info={info}
        colors={colors}
      />

      <main className="main">
        <Header search={search} onSearch={setSearch} sort={sort} onSort={setSort} />

        {error && (
          <div className="banner banner-error" role="alert">
            <span>{error}</span>
            <button className="btn btn-ghost" onClick={refresh}>
              Retry
            </button>
          </div>
        )}

        <StatCards stats={stats} />

        <QuickAdd
          categories={categories}
          defaultCategory={category}
          onAdd={(todo) => mutate(() => api.createTodo(todo))}
        />

        <TodoList
          todos={todos}
          loading={loading}
          view={view}
          category={category}
          search={search}
          completedCount={stats.completed}
          colors={colors}
          onToggle={(t) => mutate(() => api.toggleTodo(t.id))}
          onEdit={setEditing}
          onDelete={(t) => mutate(() => api.deleteTodo(t.id))}
          onClearCompleted={() => mutate(api.clearCompleted)}
        />
      </main>

      {editing && (
        <TodoModal
          todo={editing}
          categories={categories}
          onClose={() => setEditing(null)}
          onSave={async (changes) => {
            await api.updateTodo(editing.id, changes)
            setEditing(null)
            await refresh()
          }}
        />
      )}
    </div>
  )
}
