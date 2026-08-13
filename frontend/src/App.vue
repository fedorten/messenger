<template>
  <router-view />
</template>

<script>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatWebSocket } from './services/websocket'
import { notificationsEnabled, showNotification } from './services/notifications'

export default {
  name: 'App',
  setup() {
    const route = useRoute()
    const router = useRouter()
    let socket = null

    // Глобальное соединение (chat_id = 0) нужно, чтобы уведомления приходили на любой странице
    const connect = () => {
      const token = localStorage.getItem('access_token')
      if (!token || socket) return

      socket = new ChatWebSocket(0, token, (data) => {
        if (data.type !== 'message_notification') return
        // В открытом чате уведомление не нужно — сообщение и так видно
        if (route.name === 'Chat' && Number(route.params.chatId) === data.chat_id) return

        showNotification({
          title: data.chat_name || data.sender_name || 'Новое сообщение',
          body: data.chat_name ? `${data.sender_name}: ${data.preview}` : data.preview,
          icon: data.sender_avatar_url,
          onClick: () => router.push(`/chat/${data.chat_id}`),
        })
      })
      socket.connect()
    }

    const disconnect = () => {
      if (socket) {
        socket.disconnect()
        socket = null
      }
    }

    onMounted(() => {
      if (notificationsEnabled.value) connect()
    })

    watch(notificationsEnabled, (enabled) => {
      if (enabled) {
        connect()
      } else {
        disconnect()
      }
    })

    onUnmounted(disconnect)
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  min-height: 100vh;
}
</style>
