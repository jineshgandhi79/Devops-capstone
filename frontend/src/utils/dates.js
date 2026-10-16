// Due dates are plain YYYY-MM-DD strings, so compare them as strings in local time.
export function localISODate(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

export function describeDueDate(dueDate, completed) {
  if (!dueDate) return null
  const today = localISODate()
  const tomorrow = localISODate(1)
  const label = new Date(`${dueDate}T00:00:00`).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
  })

  if (completed) return { label, tone: 'muted' }
  if (dueDate < today) return { label: `Overdue · ${label}`, tone: 'danger' }
  if (dueDate === today) return { label: 'Today', tone: 'warning' }
  if (dueDate === tomorrow) return { label: 'Tomorrow', tone: 'info' }
  return { label, tone: 'default' }
}

export function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}
