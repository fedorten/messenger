import { ref } from 'vue'

const STORAGE_KEY = 'theme'
const THEMES = ['dark', 'light']

const detectTheme = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (THEMES.includes(saved)) return saved
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

export const theme = ref(detectTheme())

export const applyTheme = (value) => {
  const next = THEMES.includes(value) ? value : 'dark'
  theme.value = next
  document.documentElement.setAttribute('data-theme', next)
  localStorage.setItem(STORAGE_KEY, next)
}

export const toggleTheme = () => {
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

export const initTheme = () => {
  applyTheme(theme.value)
}
