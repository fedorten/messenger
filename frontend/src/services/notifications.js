import { ref } from 'vue'

const STORAGE_KEY = 'push_notifications_enabled'

const supported = () => typeof window !== 'undefined' && 'Notification' in window

export const notificationsSupported = supported()

export const notificationsEnabled = ref(
  supported() &&
    Notification.permission === 'granted' &&
    localStorage.getItem(STORAGE_KEY) !== 'false'
)

export const permissionState = ref(supported() ? Notification.permission : 'unsupported')

export const enableNotifications = async () => {
  if (!supported()) return false
  let permission = Notification.permission
  if (permission === 'default') {
    permission = await Notification.requestPermission()
  }
  permissionState.value = permission
  const granted = permission === 'granted'
  notificationsEnabled.value = granted
  localStorage.setItem(STORAGE_KEY, String(granted))
  return granted
}

export const disableNotifications = () => {
  notificationsEnabled.value = false
  localStorage.setItem(STORAGE_KEY, 'false')
}

/**
 * Показать пуш-уведомление. Возвращает false, если показать нельзя
 * (нет поддержки, нет разрешения или уведомления отключены пользователем).
 */
export const showNotification = ({ title, body, icon, onClick }) => {
  if (!supported() || !notificationsEnabled.value || Notification.permission !== 'granted') {
    return false
  }
  try {
    const notification = new Notification(title, {
      body,
      icon: icon || '/vite.svg',
      tag: title,
    })
    notification.onclick = () => {
      window.focus()
      notification.close()
      if (onClick) onClick()
    }
    return true
  } catch (e) {
    console.error('Notification error:', e)
    return false
  }
}
