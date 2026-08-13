import { ref } from 'vue'

const STORAGE_KEY = 'user_timezone'

const browserTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch (e) {
    return 'UTC'
  }
}

const isSupported = (timezone) => {
  if (!timezone) return false
  try {
    new Intl.DateTimeFormat('ru-RU', { timeZone: timezone })
    return true
  } catch (e) {
    return false
  }
}

// Часовой пояс пользователя из профиля: применяется ко всему отображаемому времени
export const userTimezone = ref(localStorage.getItem(STORAGE_KEY) || browserTimezone())

export const setUserTimezone = (timezone) => {
  if (!isSupported(timezone)) return
  userTimezone.value = timezone
  localStorage.setItem(STORAGE_KEY, timezone)
}

const zone = () => (isSupported(userTimezone.value) ? userTimezone.value : browserTimezone())

// Бэкенд отдаёт UTC; старые записи могут быть без суффикса зоны
const parseDate = (value) => {
  if (value instanceof Date) return value
  if (typeof value !== 'string') return new Date(value)
  const normalized = /(Z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`
  return new Date(normalized)
}

export const formatTime = (value) => {
  const date = parseDate(value)
  if (isNaN(date)) return ''
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: zone(),
  })
}

export const formatDate = (value) => {
  const date = parseDate(value)
  if (isNaN(date)) return ''
  return date.toLocaleDateString('ru-RU', { timeZone: zone() })
}

export const formatDateTime = (value) => {
  const date = parseDate(value)
  if (isNaN(date)) return ''
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: zone(),
  })
}

export const formatRelative = (value) => {
  const date = parseDate(value)
  if (isNaN(date)) return ''
  const minutes = Math.floor((Date.now() - date.getTime()) / 60000)
  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин назад`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ч назад`
  return formatDate(date)
}

export { parseDate }
