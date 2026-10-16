// Relative URLs by default: Nginx (docker-compose), the Ingress (Kubernetes)
// and the Vite dev proxy all route /api to the FastAPI backend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join(', ')
    } catch {
      // keep the HTTP status text
    }
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  listTodos: (params) => request(`/api/todos?${new URLSearchParams(params)}`),
  stats: () => request('/api/todos/stats'),
  info: () => request('/api/info'),
  createTodo: (todo) => request('/api/todos', { method: 'POST', body: JSON.stringify(todo) }),
  updateTodo: (id, changes) =>
    request(`/api/todos/${id}`, { method: 'PUT', body: JSON.stringify(changes) }),
  toggleTodo: (id) => request(`/api/todos/${id}/toggle`, { method: 'PATCH' }),
  deleteTodo: (id) => request(`/api/todos/${id}`, { method: 'DELETE' }),
  clearCompleted: () => request('/api/todos/completed', { method: 'DELETE' }),
}
