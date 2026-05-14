<template>
  <div class="chat-container">
    <header class="chat-header">
      <button @click="goBack" class="back-btn" aria-label="Назад">‹</button>
      <div class="chat-title" @click="isAdmin && !isEditingName && (isEditingName = true)">
        <h2 v-if="!isEditingName">{{ chatName }}</h2>
        <input 
          v-else 
          v-model="editedName" 
          @blur="saveChatName" 
          @keyup.enter="saveChatName"
          @keyup.esc="cancelEditName"
          class="name-input"
          maxlength="50"
          autofocus
        />
</div>
      <div class="header-actions">
        <button
          v-if="!isGroupChat && !isBotChat"
          @click="startCall('audio')"
          class="call-btn"
          title="Позвонить"
          aria-label="Позвонить"
        >
          <span>☎</span>
        </button>
        <button
          v-if="!isGroupChat && !isBotChat"
          @click="startCall('video')"
          class="call-btn video-call-btn"
          title="Видеозвонок"
          aria-label="Видеозвонок"
        >
          <span>▣</span>
        </button>
        <button
          v-if="isGroupChat"
          @click="showGroupMembers = true"
          class="members-btn"
          title="Участники"
        >
          👥
        </button>
        <button
          v-if="isGroupChat && isAdmin"
          @click="showAddMembers = true"
          class="add-members-btn"
          title="Добавить"
        >
          +
        </button>
        <button
          v-if="isGroupChat && isAdmin"
          @click="isEditingName = true"
          class="settings-btn"
          title="Настройки"
        >
          ⚙️
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else class="chat-content">
      <div ref="messagesContainer" class="messages-container" @scroll="handleScroll">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', { 'own-message': message.sender_id === currentUserId }]"
        >
          <div class="avatar-wrapper">
            <img 
              v-if="message.sender?.avatar_url" 
              :src="message.sender.avatar_url" 
              :class="['message-avatar', getAvatarClass(message)]"
            />
            <div v-else :class="['message-avatar-placeholder', getAvatarClass(message)]">
              {{ getSenderInitials(message) }}
            </div>
            <span v-if="message.sender_id !== currentUserId && isUserOnline(message.sender_id)" class="online-indicator"></span>
          </div>
          <div class="message-body">
            <div class="message-header">
              <span class="sender-name-wrapper">
                <strong :style="getSenderStyle(message)">{{ getSenderName(message) }}</strong>
                <span v-if="message.sender?.is_verified" class="verified-badge" title="Верифицирован">✓</span>
                <span v-if="isSenderUltra(message)" class="ultra-badge-small">⚡</span>
              </span>
              <div class="message-actions">
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.sender_id === currentUserId" class="read-status">
                  {{ message.is_read ? '✓✓' : '✓' }}
                </span>
                <button 
                  v-if="message.sender_id === currentUserId"
                  @click.stop="deleteMessage(message)"
                  class="delete-btn"
                  title="Удалить"
                >
                  ×
                </button>
              </div>
            </div>
          <div v-if="message.media_type" class="message-media">
            <img 
              v-if="message.media_type === 'image'" 
              :src="message.media_url" 
              :alt="message.media_filename"
              class="media-image"
              @click="openMediaModal(message)"
            />
            <div v-else-if="message.media_type === 'audio'" class="media-audio">
              <span class="voice-wave" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>
              <audio :src="message.media_url" controls></audio>
            </div>
            <div v-else-if="message.media_type === 'document'" class="media-document">
              <a :href="message.media_url" :download="message.media_filename" class="document-link">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
                <span>{{ message.media_filename }}</span>
              </a>
            </div>
          </div>
          <div class="message-content">{{ message.content }}</div>
          </div>
        </div>
      </div>

      <div v-if="typingUser" class="typing-indicator">
        <span>{{ typingUser }} печатает</span><i></i><i></i><i></i>
      </div>

      <!-- Incoming Call Modal -->
      <div v-if="incomingCall" class="call-modal incoming-call">
        <div class="call-content">
          <div class="call-avatar">{{ getCallInitials(incomingCall.from_user_name) }}</div>
          <div class="call-status">Входящий звонок</div>
          <div class="call-user">{{ incomingCall.from_user_name || 'Пользователь' }}</div>
          <div class="call-actions">
            <button @click="declineCall" class="decline-btn" aria-label="Отклонить">✕</button>
            <button @click="acceptCall" class="accept-btn" aria-label="Принять">✓</button>
          </div>
        </div>
      </div>

      <!-- Active Call Modal -->
      <div v-else-if="inCall" class="call-modal">
        <div :class="['call-panel', { 'video-call': showsVideoStage }]">
          <div v-if="showsVideoStage" class="video-stage">
            <video ref="remoteVideoRef" class="remote-video" autoplay playsinline></video>
            <video ref="localVideoRef" class="local-video" autoplay muted playsinline></video>
            <div v-if="callStatus !== 'connected'" class="video-placeholder">
              {{ remoteUser?.name || 'Пользователь' }}
            </div>
          </div>
          <div v-else class="call-info">
            <div class="call-avatar">{{ getCallInitials(remoteUser?.name) }}</div>
            <div class="call-user">{{ remoteUser?.name || 'Пользователь' }}</div>
            <div class="call-status">
              <span v-if="callStatus === 'calling'">Звоним...</span>
              <span v-else-if="callStatus === 'connecting'">Подключение...</span>
              <span v-else-if="callStatus === 'connected'">Соединено</span>
              <span v-else>Звонок</span>
            </div>
          </div>
          <div class="call-controls">
            <button @click="toggleMute" :class="['call-control-btn', { active: isMuted }]" aria-label="Микрофон">
              {{ isMuted ? '⌁' : '♪' }}
            </button>
            <button
              v-if="canToggleCamera"
              @click="toggleCamera"
              :class="['call-control-btn', { active: !isCameraOn }]"
              aria-label="Камера"
            >
              ▣
            </button>
            <button @click="endCall" class="end-call-btn" aria-label="Завершить">✕</button>
          </div>
        </div>
        <audio ref="audioRef" autoplay></audio>
      </div>

      <div class="input-container">
        <label class="attach-btn">
          <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            accept="image/*,audio/*,.pdf,.doc,.docx,.txt"
            hidden
          />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
          </svg>
        </label>
        <button @click="openDrawingModal" class="draw-btn" type="button" title="Нарисовать">
          ✎
        </button>
        <input
          v-model="newMessage"
          type="text"
          placeholder="Введите сообщение..."
          @keyup.enter="sendMessage"
          @input="handleTyping"
        />
        <button
          @click="toggleVoiceRecording"
          :class="['voice-btn', { recording: isRecording }]"
          type="button"
          :title="isRecording ? 'Остановить запись' : 'Голосовое сообщение'"
          aria-label="Голосовое сообщение"
        >
          {{ isRecording ? '■' : '●' }}
        </button>
        <button @click="sendToAI" class="ai-btn" title="Отправить ИИ">
          ✨
        </button>
        <button
          @click="sendMessage"
          :disabled="!newMessage.trim() && !selectedFile"
          class="send-btn"
          aria-label="Отправить"
        >
          <span class="send-text">Отправить</span>
          <span class="send-icon">➤</span>
        </button>
      </div>
      <div v-if="isRecording" class="recording-indicator">
        <span class="recording-dot"></span>
        <span>Идёт запись голосового сообщения</span>
        <span class="recording-time">{{ recordingTime }}с</span>
      </div>
      <div v-if="selectedFile" class="file-preview">
        <span class="file-name">{{ selectedFile.name }}</span>
        <button @click="clearFile" class="clear-file">×</button>
      </div>
    </div>

    <div v-if="showDrawingModal" class="modal-overlay" @click.self="closeDrawingModal">
      <div class="modal-content drawing-modal">
        <div class="modal-header">
          <h3>Рисунок</h3>
          <button @click="closeDrawingModal" class="close-btn">×</button>
        </div>
        <div class="drawing-toolbar">
          <label class="drawing-control">
            <span>Цвет</span>
            <input v-model="drawingColor" type="color" />
          </label>
          <label class="drawing-control drawing-size-control">
            <span>Карандаш</span>
            <input v-model.number="drawingSize" type="range" min="2" max="40" />
            <span class="drawing-size-value">{{ drawingSize }}</span>
          </label>
          <button @click="clearDrawingCanvas" class="drawing-action-btn drawing-clear-btn" type="button">
            Очистить
          </button>
        </div>
        <canvas
          ref="drawingCanvas"
          class="drawing-canvas"
          @pointerdown="startDrawing"
          @pointermove="drawOnCanvas"
          @pointerup="stopDrawing"
          @pointercancel="stopDrawing"
          @pointerleave="stopDrawing"
        ></canvas>
        <div class="modal-actions">
          <button @click="closeDrawingModal" class="drawing-action-btn drawing-cancel-btn">Отмена</button>
          <button @click="attachDrawing" class="drawing-action-btn drawing-attach-btn">Прикрепить</button>
        </div>
      </div>
    </div>

    <!-- AI Modal -->
    <div v-if="showAIModal" class="modal-overlay" @click.self="showAIModal = false">
      <div class="modal-content ai-modal">
        <div class="modal-header">
          <h3>{{ aiMode === 'chat' ? 'Чат с ИИ' : 'Редактирование сообщения' }}</h3>
          <button @click="showAIModal = false" class="close-btn">×</button>
        </div>
        
        <div v-if="aiMode === 'edit'" class="ai-edit-mode">
          <div class="form-group">
            <label>Введи запрос:</label>
            <textarea 
              v-model="aiEditPrompt" 
              placeholder="Опиши как изменить сообщение..."
              class="input"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label>Твой текст:</label>
            <textarea 
              v-model="aiEditText" 
              placeholder="Текст для изменения"
              class="input"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label>Результат:</label>
            <textarea 
              v-model="aiResult" 
              placeholder="Здесь появится отредактированное сообщение"
              class="input"
              readonly
            ></textarea>
          </div>
          
          <div class="modal-actions">
            <button @click="showAIModal = false" class="btn-secondary">Отмена</button>
            <button 
              @click="applyAIEdit" 
              class="btn-primary"
            >Отправить</button>
            <button 
              v-if="aiResult"
              @click="applyAIResult" 
              class="btn-primary"
            >Применить</button>
          </div>
        </div>
        
        <div v-else class="ai-chat-mode">
          <p class="ai-hint">Напиши что хочешь спросить у ИИ</p>
          <button @click="sendAIChat" class="btn-primary">Отправить вопрос</button>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления участников -->
    <div v-if="showAddMembers" class="modal-overlay" @click.self="showAddMembers = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Добавить участников</h3>
          <button @click="showAddMembers = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Поиск пользователей:</label>
            <input
              v-model="memberSearchQuery"
              type="text"
              placeholder="Начните вводить имя или email..."
              @input="handleMemberSearch"
            />
            <div v-if="memberSearchResults.length > 0" class="member-search-results">
              <div
                v-for="user in memberSearchResults"
                :key="user.id"
                class="member-item"
                @click="toggleAddMember(user)"
              >
                <div class="member-info">
                  <strong>{{ user.full_name || user.email }}</strong>
                  <span class="member-email">{{ user.email }}</span>
                </div>
                <div class="checkbox" :class="{ checked: isAddMemberSelected(user.id) }">
                  {{ isAddMemberSelected(user.id) ? '✓' : '' }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="membersToAdd.length > 0" class="selected-members">
            <div class="selected-label">Выбранные участники ({{ membersToAdd.length }}):</div>
            <div class="selected-tags">
              <span
                v-for="member in membersToAdd"
                :key="member.id"
                class="member-tag"
              >
                {{ member.full_name || member.email }}
                <button @click="removeAddMember(member.id)" class="remove-member">×</button>
              </span>
            </div>
          </div>
          <div v-if="addMemberError" class="error">{{ addMemberError }}</div>
        </div>
        <div class="modal-footer">
          <button @click="showAddMembers = false" class="cancel-btn">Отмена</button>
          <button
            @click="addMembersToGroup"
            :disabled="membersToAdd.length === 0 || addingMembers"
            class="create-btn"
          >
            {{ addingMembers ? 'Добавление...' : 'Добавить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно участников группы -->
    <div v-if="showGroupMembers" class="modal-overlay" @click.self="showGroupMembers = false">
      <div class="modal-content members-modal">
        <div class="modal-header">
          <h3>Участники группы</h3>
          <button @click="showGroupMembers = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="members-list">
            <div 
              v-for="member in currentChat?.members" 
              :key="member.id"
              class="member-row"
            >
              <div class="member-info">
                <strong>{{ member.user?.full_name || member.user?.email }}</strong>
                <span class="member-role">{{ member.role === 'admin' ? 'Админ' : 'Участник' }}</span>
              </div>
              <div v-if="isAdmin && member.user_id !== currentUserId" class="member-actions">
                <button 
                  @click="toggleRole(member)"
                  class="role-btn"
                  :title="member.role === 'admin' ? 'Понизить' : 'Назначить админом'"
                >
                  {{ member.role === 'admin' ? '⬇' : '⬆' }}
                </button>
                <button 
                  @click="removeMemberFromGroup(member)"
                  class="remove-btn"
                  title="Удалить"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!isAdmin" class="modal-footer">
          <button @click="leaveGroup" class="leave-btn">Покинуть группу</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, shallowRef, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chatsAPI, messagesAPI, authAPI } from '../services/api'
import { ChatWebSocket } from '../services/websocket'

export default {
  name: 'Chat',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const chatId = parseInt(route.params.chatId)
    const messages = ref([])
    const loading = ref(true)
    const newMessage = ref('')
    const chatName = ref('Чат')
    const currentUserId = ref(null)
    const currentUser = ref(null)  // Для хранения полных данных пользователя
    const messagesContainer = ref(null)
    const ws = ref(null)
    const shouldAutoScroll = ref(true)
    const isGroupChat = ref(false)
    const isBotChat = ref(false)
    const currentBot = ref(null)
    const isAdmin = ref(false)
    const isEditingName = ref(false)
    const editedName = ref('')
    const showGroupMembers = ref(false)
    const showAddMembers = ref(false)
    const memberSearchQuery = ref('')
    const memberSearchResults = ref([])
    const membersToAdd = ref([])
    const addingMembers = ref(false)
    const addMemberError = ref('')
    const currentChat = ref(null)
    const fileInput = ref(null)
    const selectedFile = ref(null)
    const uploading = ref(false)
    const showDrawingModal = ref(false)
    const drawingCanvas = ref(null)
    const drawingColor = ref('#7c3aed')
    const drawingSize = ref(6)
    const isDrawing = ref(false)
    const lastDrawingPoint = ref(null)
    const onlineUsers = ref(new Set())
    const typingUser = ref(null)
    let typingTimeout = null
    let pollInterval = null
    
    // Call state
    const inCall = ref(false)
    const callStatus = ref('') // 'calling', 'ringing', 'connected', 'ended'
    const remoteUser = ref(null)
    const localStream = shallowRef(null)
    const remoteStream = shallowRef(null)
    const peerConnection = shallowRef(null)
    const incomingCall = ref(null)
    const audioRef = ref(null)
    const localVideoRef = ref(null)
    const remoteVideoRef = ref(null)
    const callMode = ref('audio')
    const isMuted = ref(false)
    const isCameraOn = ref(false)
    const canToggleCamera = ref(false)
    const hasRemoteVideo = ref(false)
    const pendingIceCandidates = ref([])
    const isRecording = ref(false)
    const recordingTime = ref(0)
    const mediaRecorder = shallowRef(null)
    const voiceChunks = ref([])
    let recordingTimer = null

    const showsVideoStage = computed(() => isCameraOn.value || hasRemoteVideo.value)

    const isUserOnline = (userId) => onlineUsers.value.has(userId)

    const getCallInitials = (name) => {
      const value = name || remoteUser.value?.name || chatName.value || 'Пользователь'
      return value
        .split(' ')
        .filter(Boolean)
        .map(part => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    }

    const getSenderInitials = (message) => {
      if (message.sender_id === 0 && isBotChat.value) {
        const botName = currentBot.value?.name || 'Бот'
        return botName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
      }
      const name = message.sender?.full_name || message.sender?.email || 'Пользователь'
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }

    const loadChat = async () => {
      try {
        const chat = await chatsAPI.getChat(chatId)
        currentChat.value = chat
        chatName.value = getChatName(chat)
        isGroupChat.value = chat.chat_type === 'group'
        isBotChat.value = chat.chat_type === 'bot'
        
        if (isBotChat.value && chat.bot) {
          currentBot.value = chat.bot
        }
        
        if (isGroupChat.value) {
          const myMember = chat.members?.find(m => m.user_id === currentUserId.value)
          isAdmin.value = myMember?.role === 'admin'
        }
      } catch (error) {
        console.error('Error loading chat:', error)
      }
    }

    const getChatName = (chat) => {
      if (chat.name) return chat.name
      if (chat.members && chat.members.length > 0) {
        const otherMember = chat.members.find(m => m.user_id !== currentUserId.value)
        if (otherMember) {
          return otherMember.user?.full_name || otherMember.user?.email || 'Пользователь'
        }
      }
      return 'Чат'
    }

    const loadMessages = async () => {
      try {
        const response = await chatsAPI.getMessages(chatId)
        messages.value = response.data || []
        await chatsAPI.markAsRead(chatId)
        shouldAutoScroll.value = true
      } catch (error) {
        console.error('Error loading messages:', error)
      } finally {
        loading.value = false
        await nextTick()
        setTimeout(() => {
          scrollToBottom(true)
        }, 100)
        setTimeout(() => {
          scrollToBottom(true)
        }, 300)
      }
    }

    const getSenderName = (message) => {
      if (message.sender_id === currentUserId.value) {
        return 'Вы'
      }
      if (message.sender_id === 0 && isBotChat.value) {
        return currentBot.value?.name || 'Бот'
      }
      return message.sender?.full_name || message.sender?.email || 'Пользователь'
    }

    const isSenderUltra = (message) => {
      if (message.sender_id === currentUserId.value) {
        return currentUser.value?.is_ultra || false
      }
      return message.sender?.is_ultra || false
    }

    const getSenderStyle = (message) => {
      const isUltra = message.sender_id === currentUserId.value 
        ? (currentUser.value?.is_ultra || false)
        : (message.sender?.is_ultra || false)
      
      if (!isUltra) return {}
      
      // For self - use localStorage. For others - use sender data from server (from DB)
      let color
      if (message.sender_id === currentUserId.value) {
        color = localStorage.getItem('ultra_profile_color')
      } else {
        // Get from sender data which comes from server/DB
        color = message.sender?.ultra_profile_color || null
      }
      
      if (!color) return {}
      
      if (color.includes('gradient')) {
        return { 
          background: color, 
          WebkitBackgroundClip: 'text', 
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }
      }
      return { color: color }
    }

    const getAvatarClass = (message) => {
      const isUltra = message.sender_id === currentUserId.value 
        ? (currentUser.value?.is_ultra || false)
        : (message.sender?.is_ultra || false)
      
      if (!isUltra) return ''
      
      // For self - use localStorage. For others - use sender data from server (from DB)
      let style
      if (message.sender_id === currentUserId.value) {
        style = localStorage.getItem('ultra_avatar_style') || 'default'
      } else {
        // Get from sender data which comes from server/DB
        style = message.sender?.ultra_avatar_style || 'default'
      }
      
      if (style === 'gold') return 'avatar-gold'
      if (style === 'border') return 'avatar-border'
      if (style === 'shine') return 'avatar-shine'
      return ''
    }

    const formatTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    }

    const openMediaModal = (message) => {
      if (message?.media_url) {
        window.open(message.media_url, '_blank', 'noopener,noreferrer')
      }
    }

    const scrollToBottom = async (force = false) => {
      if (!force && !shouldAutoScroll.value) return
      
      await nextTick()
      if (messagesContainer.value) {
        const container = messagesContainer.value
        // Используем несколько попыток для надежной прокрутки
        const scroll = () => {
          if (container) {
            const maxScroll = container.scrollHeight - container.clientHeight
            container.scrollTop = maxScroll > 0 ? maxScroll : container.scrollHeight
          }
        }
        // Прокручиваем сразу
        scroll()
        // И еще раз через небольшую задержку для надежности
        requestAnimationFrame(() => {
          scroll()
          // И еще раз после следующего кадра
          requestAnimationFrame(() => {
            scroll()
            // И еще раз для полной уверенности
            setTimeout(() => {
              scroll()
            }, 50)
          })
        })
      }
    }
    
    // Отслеживаем скролл, чтобы определить, нужно ли автоматически прокручивать
    const handleScroll = () => {
      if (!messagesContainer.value) return
      const container = messagesContainer.value
      const threshold = 100 // пикселей от низа
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold
      shouldAutoScroll.value = isNearBottom
    }

    const sendMessageWithMedia = async (content, mediaData = null) => {
      if (ws.value && ws.value.ws && ws.value.ws.readyState === WebSocket.OPEN) {
        ws.value.sendMessage(content, mediaData)
        return null
      }

      const message = await messagesAPI.sendMessage(chatId, content, mediaData)
      messages.value.push(message)
      scrollToBottom()
      return message
    }

    const sendMessage = async () => {
      const hasText = newMessage.value.trim()
      const hasFile = selectedFile.value

      if (!hasText && !hasFile) return

      let mediaData = null

      if (hasFile) {
        uploading.value = true
        console.log('Uploading file:', selectedFile.value.name, selectedFile.value.type, selectedFile.value.size)
        try {
          const uploadResult = await messagesAPI.uploadMedia(selectedFile.value)
          console.log('Upload result:', uploadResult)
          mediaData = uploadResult
        } catch (error) {
          console.error('Error uploading file:', error)
          alert('Ошибка загрузки файла')
          uploading.value = false
          return
        }
        uploading.value = false
      }

      const content = hasText ? newMessage.value.trim() : (mediaData?.media_filename || 'Файл')
      console.log('Sending message - content:', content, 'mediaData:', mediaData)
      newMessage.value = ''

      if (ws.value && ws.value.ws && ws.value.ws.readyState === WebSocket.OPEN) {
        const tempId = `temp-${Date.now()}-${Math.random()}`
        const tempMessage = {
          id: tempId,
          chat_id: chatId,
          sender_id: currentUserId.value,
          sender: { 
            id: currentUserId.value, 
            email: currentUser.value?.email || '', 
            full_name: 'Вы',
            is_ultra: currentUser.value?.is_ultra || false,
            ultra_profile_color: localStorage.getItem('ultra_profile_color'),
            ultra_avatar_style: localStorage.getItem('ultra_avatar_style'),
          },
          content: content,
          media_type: mediaData?.media_type || null,
          media_filename: mediaData?.media_filename || null,
          media_url: mediaData?.media_url || null,
          media_size: mediaData?.media_size || null,
          created_at: new Date().toISOString(),
          edited_at: null,
          isTemp: true,
          tempId: tempId,
        }
        messages.value.push(tempMessage)
        scrollToBottom()
        
        try {
          console.log('Sending via WebSocket - content:', content, 'mediaData:', mediaData)
          ws.value.sendMessage(content, mediaData)
          clearFile()
        } catch (error) {
          const index = messages.value.findIndex(m => m.tempId === tempId)
          if (index !== -1) {
            messages.value.splice(index, 1)
          }
          console.error('Error sending message via WebSocket:', error)
          try {
            const message = await messagesAPI.sendMessage(chatId, content, mediaData)
            messages.value.push(message)
            scrollToBottom()
          } catch (apiError) {
            console.error('Error sending message via API:', apiError)
            alert('Ошибка отправки сообщения')
          }
        }
      } else {
        console.log('WebSocket not connected, using API')
        try {
          const message = await messagesAPI.sendMessage(chatId, content, mediaData)
          messages.value.push(message)
          if (isBotChat.value) {
            const response = await chatsAPI.getMessages(chatId)
            messages.value = response.data || messages.value
          }
          scrollToBottom()
          clearFile()
        } catch (error) {
          console.error('Error sending message:', error)
          alert('Ошибка отправки сообщения')
        }
      }
    }
    
    const showAIModal = ref(false)
    const aiEditText = ref('')
    const aiEditPrompt = ref('')
    const aiMode = ref('edit')
    const aiResult = ref('')
    
    const sendToAI = async () => {
      // Always show edit mode first
      showAIModal.value = true
      aiMode.value = 'edit'
      aiEditText.value = newMessage.value.trim()
      aiEditPrompt.value = ''
    }
    
    const applyAIEdit = async () => {
      const prompt = aiEditPrompt.value
      const text = aiEditText.value
      
      if (!prompt.trim() || !text.trim()) {
        alert('Заполни оба поля!')
        return
      }
      
      const fullPrompt = prompt + ': ' + text
      
      try {
        const token = localStorage.getItem('access_token')
        
        const response = await fetch('/api/v1/messages/ai/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
          },
          body: JSON.stringify({ message: fullPrompt })
        })
        
        if (!response.ok) {
          alert('Ошибка: ' + response.status)
          return
        }
        
        const res = await response.json()
        
        if (res.response) {
          aiResult.value = res.response
        }
        
      } catch (e) {
        alert('Ошибка: ' + e.message)
      }
    }
    
    const applyAIResult = () => {
      if (aiResult.value) {
        newMessage.value = aiResult.value
        showAIModal.value = false
        aiEditText.value = ''
        aiEditPrompt.value = ''
        aiResult.value = ''
      }
    }
    
    const sendAIChat = async () => {
      const text = newMessage.value.trim()
      if (!text) return
      
      // Show user message in chat temporarily
      const tempId = `temp-${Date.now()}`
      messages.value.push({
        id: tempId,
        chat_id: chatId,
        sender_id: currentUserId.value,
        sender: { id: currentUserId.value, full_name: 'Вы' },
        content: text,
        created_at: new Date().toISOString(),
        isTemp: true
      })
      newMessage.value = ''
      scrollToBottom()
      
      try {
        const res = await messagesAPI.chatWithAI(text)
        // Add AI response
        messages.value.push({
          id: `ai-${Date.now()}`,
          chat_id: chatId,
          sender_id: 0,
          sender: null,
          content: res.response,
          created_at: new Date().toISOString()
        })
        scrollToBottom()
      } catch (e) {
        console.error('AI error:', e)
        alert('Ошибка ИИ')
      }
    }

    const handleTyping = () => {
      if (ws.value) {
        ws.value.sendTyping()
      }
    }

    const handleFileSelect = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        alert('Файл слишком большой. Максимальный размер - 10 МБ')
        event.target.value = ''
        return
      }

      selectedFile.value = file
      event.target.value = ''
    }

    const stopRecordingTimer = () => {
      if (recordingTimer) {
        clearInterval(recordingTimer)
        recordingTimer = null
      }
    }

    const startVoiceRecording = async () => {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        alert('Запись голоса не поддерживается в этом браузере')
        return
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        const recorderOptions = MediaRecorder.isTypeSupported('audio/webm')
          ? { mimeType: 'audio/webm' }
          : {}
        const recorder = new MediaRecorder(stream, recorderOptions)
        voiceChunks.value = []
        mediaRecorder.value = recorder
        recordingTime.value = 0

        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            voiceChunks.value.push(event.data)
          }
        }

        recorder.onstop = async () => {
          stopRecordingTimer()
          stream.getTracks().forEach(track => track.stop())
          isRecording.value = false

          const blob = new Blob(voiceChunks.value, { type: recorder.mimeType || 'audio/webm' })
          voiceChunks.value = []
          mediaRecorder.value = null

          if (!blob.size) return

          const extension = blob.type.includes('ogg') ? 'ogg' : 'webm'
          const file = new File([blob], `voice-${Date.now()}.${extension}`, { type: blob.type })
          try {
            const mediaData = await messagesAPI.uploadMedia(file)
            await sendMessageWithMedia(mediaData.media_filename || 'Голосовое сообщение', mediaData)
          } catch (error) {
            console.error('Error sending voice message:', error)
            alert('Не удалось отправить голосовое сообщение')
          }
        }

        recorder.start()
        isRecording.value = true
        recordingTimer = setInterval(() => {
          recordingTime.value += 1
        }, 1000)
      } catch (error) {
        console.error('Voice recording error:', error)
        alert('Не удалось получить доступ к микрофону')
      }
    }

    const stopVoiceRecording = () => {
      if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
        mediaRecorder.value.stop()
      }
    }

    const toggleVoiceRecording = () => {
      if (isRecording.value) {
        stopVoiceRecording()
      } else {
        startVoiceRecording()
      }
    }

    const clearFile = () => {
      selectedFile.value = null
    }

    const prepareDrawingCanvas = () => {
      const canvas = drawingCanvas.value
      if (!canvas) return

      const ratio = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()
      canvas.width = Math.max(1, Math.floor(rect.width * ratio))
      canvas.height = Math.max(1, Math.floor(rect.height * ratio))

      const ctx = canvas.getContext('2d')
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, rect.width, rect.height)
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
    }

    const openDrawingModal = async () => {
      showDrawingModal.value = true
      await nextTick()
      prepareDrawingCanvas()
    }

    const closeDrawingModal = () => {
      showDrawingModal.value = false
      isDrawing.value = false
      lastDrawingPoint.value = null
    }

    const getCanvasPoint = (event) => {
      const canvas = drawingCanvas.value
      const rect = canvas.getBoundingClientRect()
      return {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      }
    }

    const startDrawing = (event) => {
      const canvas = drawingCanvas.value
      if (!canvas) return

      event.preventDefault()
      canvas.setPointerCapture?.(event.pointerId)
      isDrawing.value = true
      const point = getCanvasPoint(event)
      lastDrawingPoint.value = point

      const ctx = canvas.getContext('2d')
      ctx.fillStyle = drawingColor.value
      ctx.beginPath()
      ctx.arc(point.x, point.y, drawingSize.value / 2, 0, Math.PI * 2)
      ctx.fill()
    }

    const drawOnCanvas = (event) => {
      if (!isDrawing.value || !lastDrawingPoint.value) return

      event.preventDefault()
      const canvas = drawingCanvas.value
      const point = getCanvasPoint(event)
      const ctx = canvas.getContext('2d')
      ctx.strokeStyle = drawingColor.value
      ctx.lineWidth = drawingSize.value
      ctx.beginPath()
      ctx.moveTo(lastDrawingPoint.value.x, lastDrawingPoint.value.y)
      ctx.lineTo(point.x, point.y)
      ctx.stroke()
      lastDrawingPoint.value = point
    }

    const stopDrawing = (event) => {
      drawingCanvas.value?.releasePointerCapture?.(event.pointerId)
      isDrawing.value = false
      lastDrawingPoint.value = null
    }

    const clearDrawingCanvas = () => {
      prepareDrawingCanvas()
    }

    const attachDrawing = async () => {
      const canvas = drawingCanvas.value
      if (!canvas) return

      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
      if (!blob) {
        alert('Не удалось сохранить рисунок')
        return
      }

      selectedFile.value = new File([blob], `drawing-${Date.now()}.png`, {
        type: 'image/png',
      })
      closeDrawingModal()
    }

    const setupWebSocket = () => {
      const token = localStorage.getItem('access_token')
      if (!token) return

      ws.value = new ChatWebSocket(
        chatId,
        token,
        (data) => {
          console.log('WebSocket message:', data)
          
          if (data.type === 'new_message') {
            const message = data.message
            nextTick(() => {
              const existingIndex = messages.value.findIndex(m => m.id === message.id)
              if (existingIndex !== -1) {
                const newMessages = [...messages.value]
                newMessages[existingIndex] = message
                messages.value = newMessages
              } else {
                const isOurMessage = message.sender_id === currentUserId.value
                const tempIndex = messages.value.findIndex(
                  m => m.isTemp && m.content === message.content && m.sender_id === message.sender_id && isOurMessage
                )
                if (tempIndex !== -1) {
                  const newMessages = [...messages.value]
                  newMessages[tempIndex] = message
                  messages.value = newMessages
                } else {
                  messages.value = [...messages.value, message]
                }
              }
              scrollToBottom()
            })
          } else if (data.type === 'user_online') {
            onlineUsers.value.add(data.user_id)
          } else if (data.type === 'user_offline') {
            onlineUsers.value.delete(data.user_id)
          } else if (data.type === 'typing') {
            if (data.user_id !== currentUserId.value) {
              typingUser.value = data.user_name || 'Пользователь'
              if (typingTimeout) clearTimeout(typingTimeout)
              typingTimeout = setTimeout(() => {
                typingUser.value = null
              }, 3000)
            }
          } else if (data.type === 'new_message') {
            const msg = data.message
            if (!messages.value.find(m => m.id === msg.id)) {
              messages.value = [...messages.value, msg]
              scrollToBottom()
            }
          } else if (data.type === 'call_offer') {
            // Only process if this call is for us
            if (Number(data.target_user_id) === currentUserId.value) {
              handleIncomingCall(data)
            }
          } else if (data.type === 'call_answer') {
            // Only process if this answer is for us
            if (Number(data.target_user_id) === currentUserId.value) {
              handleCallAnswer(data)
            }
          } else if (data.type === 'call_ice') {
            // Only process if this ICE is for us
            if (Number(data.target_user_id) === currentUserId.value) {
              handleRemoteIce(data)
            }
          } else if (data.type === 'call_end') {
            // Only process if this end is for us
            if (Number(data.target_user_id) === currentUserId.value) {
              endCall(false)
            }
          }
        },
        (error) => {
          console.error('WebSocket error:', error)
        }
      )

      ws.value.connect()
    }

    // Call functions
    const getOtherUserId = () => {
      if (!currentChat.value || isGroupChat.value) return null
      const other = currentChat.value.members?.find(m => m.user_id !== currentUserId.value)
      return other?.user_id || null
    }

    const attachRemoteStream = (stream) => {
      remoteStream.value = stream
      hasRemoteVideo.value = stream.getVideoTracks().length > 0
      if (audioRef.value) {
        audioRef.value.srcObject = stream
        audioRef.value.play?.().catch(() => {})
      }
      if (remoteVideoRef.value) {
        remoteVideoRef.value.srcObject = stream
        remoteVideoRef.value.play?.().catch(() => {})
      }
    }

    const syncLocalMediaState = () => {
      const audioTrack = localStream.value?.getAudioTracks?.()[0] || null
      const videoTrack = localStream.value?.getVideoTracks?.()[0] || null
      isMuted.value = audioTrack ? !audioTrack.enabled : false
      canToggleCamera.value = Boolean(videoTrack)
      isCameraOn.value = Boolean(videoTrack?.enabled)
    }

    const createLocalStream = async (cameraEnabled = false) => {
      const constraints = cameraEnabled
        ? { audio: true, video: true }
        : { audio: true, video: false }

      try {
        localStream.value = await navigator.mediaDevices.getUserMedia(constraints)
        localStream.value.getVideoTracks().forEach(track => {
          track.enabled = cameraEnabled
        })
      } catch (error) {
        if (!cameraEnabled) {
          throw error
        }
        localStream.value = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      }

      syncLocalMediaState()
      return localStream.value
    }

    const attachLocalStream = async () => {
      await nextTick()
      if (localVideoRef.value && localStream.value) {
        localVideoRef.value.srcObject = localStream.value
        localVideoRef.value.play?.().catch(() => {})
      }
    }

    const attachCallStreams = async () => {
      await attachLocalStream()
      await nextTick()
      if (audioRef.value && remoteStream.value) {
        audioRef.value.srcObject = remoteStream.value
        audioRef.value.play?.().catch(() => {})
      }
      if (remoteVideoRef.value && remoteStream.value) {
        remoteVideoRef.value.srcObject = remoteStream.value
        remoteVideoRef.value.play?.().catch(() => {})
      }
    }

    const createPeerConnection = (targetUserId) => {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      })

      pc.ontrack = (event) => {
        if (event.streams[0]) {
          attachRemoteStream(event.streams[0])
        }
      }

      pc.onicecandidate = (event) => {
        if (event.candidate && ws.value?.ws) {
          ws.value.ws.send(JSON.stringify({
            type: 'call_ice',
            target_user_id: targetUserId,
            candidate: event.candidate
          }))
        }
      }

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'connected') {
          callStatus.value = 'connected'
        }
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          callStatus.value = 'ended'
        }
      }

      return pc
    }

    const flushPendingIceCandidates = async () => {
      if (!peerConnection.value || !pendingIceCandidates.value.length) return

      const candidates = [...pendingIceCandidates.value]
      pendingIceCandidates.value = []

      for (const candidate of candidates) {
        try {
          await peerConnection.value.addIceCandidate(new RTCIceCandidate(candidate))
        } catch (error) {
          console.error('Error applying queued ICE candidate:', error)
        }
      }
    }

    const startCall = async (mode = 'audio') => {
      const targetUserId = getOtherUserId()
      if (!targetUserId) {
        alert('Звонки доступны только в личных чатах')
        return
      }

      if (!ws.value || !ws.value.ws || ws.value.ws.readyState !== WebSocket.OPEN) {
        alert('Подключение не установлено. Попробуйте позже.')
        return
      }

      try {
        callMode.value = mode === 'video' ? 'video' : 'audio'
        await createLocalStream(callMode.value === 'video')
        
        peerConnection.value = createPeerConnection(targetUserId)

        localStream.value.getTracks().forEach(track => {
          peerConnection.value.addTrack(track, localStream.value)
        })

        const offer = await peerConnection.value.createOffer()
        await peerConnection.value.setLocalDescription(offer)

        inCall.value = true
        callStatus.value = 'calling'
        remoteUser.value = { id: targetUserId }
        await attachCallStreams()

        ws.value.ws.send(JSON.stringify({
          type: 'call_offer',
          target_user_id: targetUserId,
          chat_id: chatId,
          call_mode: callMode.value,
          sdp: peerConnection.value.localDescription
        }))

      } catch (error) {
        console.error('Error starting call:', error)
        alert('Не удалось начать звонок: ' + error.message)
        endCall()
      }
    }

    const handleIncomingCall = (data) => {
      console.log('Incoming call:', data)
      callMode.value = data.call_mode === 'video' ? 'video' : 'audio'
      incomingCall.value = data
      // Play ringtone
      const ringtone = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleR4HLp3W6p97IRc2iNLrsYsdHDiMxemmVB8NNY3P6bJOHB08jMTrr1IcHD+L0OqxUB0fP4rP6bFSHSBCh87rsFEcIEEEAtLqsFAdIEGFAtLqsFAdIEEAAAAAA==')
      ringtone.loop = true
      ringtone.volume = 0.5
      ringtone.play().catch(() => {})
      incomingCall.value.ringtone = ringtone
    }

    const acceptCall = async () => {
      const data = incomingCall.value
      if (!data) return
      if (data.ringtone) {
        data.ringtone.pause()
        data.ringtone = null
      }
      incomingCall.value = null

      try {
        callMode.value = data.call_mode === 'video' ? 'video' : 'audio'
        inCall.value = true
        callStatus.value = 'connecting'
        remoteUser.value = { id: data.from_user_id, name: data.from_user_name }
        await createLocalStream(callMode.value === 'video')
        
        peerConnection.value = createPeerConnection(data.from_user_id)

        localStream.value.getTracks().forEach(track => {
          peerConnection.value.addTrack(track, localStream.value)
        })

        await peerConnection.value.setRemoteDescription(new RTCSessionDescription(data.sdp))
        const answer = await peerConnection.value.createAnswer()
        await peerConnection.value.setLocalDescription(answer)
        await flushPendingIceCandidates()

        callStatus.value = 'connected'
        await attachCallStreams()

        ws.value.ws.send(JSON.stringify({
          type: 'call_answer',
          target_user_id: data.from_user_id,
          accepted: true,
          call_mode: callMode.value,
          sdp: peerConnection.value.localDescription
        }))
      } catch (error) {
        console.error('Error accepting call:', error)
        alert('Не удалось принять звонок: ' + (error.message || 'ошибка доступа к микрофону/камере'))
        endCall()
      }
    }

    const declineCall = () => {
      const data = incomingCall.value
      if (data) {
        if (data.ringtone) {
          data.ringtone.pause()
          data.ringtone = null
        }
        if (ws.value?.ws) {
          ws.value.ws.send(JSON.stringify({
            type: 'call_answer',
            target_user_id: data.from_user_id,
            accepted: false
          }))
        }
      }
      incomingCall.value = null
    }

    const handleCallAnswer = async (data) => {
      console.log('Call answer received:', data)
      if (!peerConnection.value) {
        console.log('No peer connection, initiating answerer side')
        try {
          callMode.value = data.call_mode === 'video' ? 'video' : 'audio'
          inCall.value = true
          callStatus.value = 'connecting'
          await createLocalStream(callMode.value === 'video')
          
          peerConnection.value = createPeerConnection(data.from_user_id)
          
          localStream.value.getTracks().forEach(track => {
            peerConnection.value.addTrack(track, localStream.value)
          })
          await attachCallStreams()
        } catch (err) {
          console.error('Error setting up peer connection:', err)
          alert('Не удалось подготовить звонок: ' + (err.message || 'ошибка доступа к микрофону/камере'))
          endCall()
          return
        }
      }

      try {
        if (data.accepted && data.sdp) {
          await peerConnection.value.setRemoteDescription(new RTCSessionDescription(data.sdp))
          await flushPendingIceCandidates()
          callStatus.value = 'connected'
        } else {
          alert('Звонок отклонён')
          endCall()
        }
      } catch (error) {
        console.error('Error handling call answer:', error)
        endCall()
      }
    }

    const handleRemoteIce = async (data) => {
      if (!data.candidate) return
      if (!peerConnection.value || !peerConnection.value.remoteDescription) {
        pendingIceCandidates.value = [...pendingIceCandidates.value, data.candidate]
        return
      }
      try {
        await peerConnection.value.addIceCandidate(new RTCIceCandidate(data.candidate))
      } catch (error) {
        console.error('Error adding ICE candidate:', error)
      }
    }

    const endCall = (notifyRemote = true) => {
      if (localStream.value) {
        localStream.value.getTracks().forEach(track => track.stop())
        localStream.value = null
      }
      if (peerConnection.value) {
        peerConnection.value.close()
        peerConnection.value = null
      }
      
      const targetId = remoteUser.value?.id || getOtherUserId()
      if (notifyRemote && targetId && ws.value?.ws) {
        ws.value.ws.send(JSON.stringify({
          type: 'call_end',
          target_user_id: targetId
        }))
      }

      inCall.value = false
      callStatus.value = ''
      remoteUser.value = null
      incomingCall.value = null
      remoteStream.value = null
      pendingIceCandidates.value = []
      callMode.value = 'audio'
      isMuted.value = false
      isCameraOn.value = false
      canToggleCamera.value = false
      hasRemoteVideo.value = false
      stopRecordingTimer()
    }

    const toggleMute = () => {
      if (!localStream.value) return
      localStream.value.getAudioTracks().forEach(track => {
        track.enabled = !track.enabled
        isMuted.value = !track.enabled
      })
    }

    const toggleCamera = () => {
      if (!localStream.value || !canToggleCamera.value) {
        alert('Камера недоступна на этом устройстве или не была разрешена.')
        return
      }
      localStream.value.getVideoTracks().forEach(track => {
        track.enabled = !track.enabled
        isCameraOn.value = track.enabled
      })
      attachCallStreams()
    }

    const handleMemberSearch = async () => {
      if (!memberSearchQuery.value.trim()) {
        memberSearchResults.value = []
        return
      }
      try {
        const { usersAPI } = await import('../services/api')
        const response = await usersAPI.search(memberSearchQuery.value)
        // Исключаем текущего пользователя и уже существующих участников
        const existingMemberIds = currentChat.value?.members?.map(m => m.user_id) || []
        const excludeIds = [currentUserId.value, ...existingMemberIds].filter(Boolean)
        memberSearchResults.value = (response.data || []).filter(u => !excludeIds.includes(u.id))
      } catch (error) {
        console.error('Member search error:', error)
        memberSearchResults.value = []
      }
    }

    const toggleAddMember = (user) => {
      const index = membersToAdd.value.findIndex(m => m.id === user.id)
      if (index === -1) {
        membersToAdd.value.push(user)
      } else {
        membersToAdd.value.splice(index, 1)
      }
    }

    const isAddMemberSelected = (userId) => {
      return membersToAdd.value.some(m => m.id === userId)
    }

    const removeAddMember = (userId) => {
      const index = membersToAdd.value.findIndex(m => m.id === userId)
      if (index !== -1) {
        membersToAdd.value.splice(index, 1)
      }
    }

    const deleteMessage = async (message) => {
      if (!confirm('Удалить сообщение?')) return
      
      try {
        await messagesAPI.deleteMessage(message.id)
        messages.value = messages.value.filter(m => m.id !== message.id)
      } catch (error) {
        console.error('Error deleting message:', error)
        alert('Ошибка удаления сообщения')
      }
    }

    const addMembersToGroup = async () => {
      if (membersToAdd.value.length === 0) {
        addMemberError.value = 'Выберите хотя бы одного участника'
        return
      }

      addingMembers.value = true
      addMemberError.value = ''

      try {
        const memberIds = membersToAdd.value.map(m => m.id)
        await chatsAPI.addMembersToGroup(chatId, memberIds)
        
        // Сброс формы и обновление чата
        showAddMembers.value = false
        memberSearchQuery.value = ''
        memberSearchResults.value = []
        membersToAdd.value = []
        await loadChat()
      } catch (error) {
        console.error('Error adding members:', error)
        addMemberError.value = error.response?.data?.detail || 'Ошибка добавления участников'
      } finally {
        addingMembers.value = false
      }
    }

    const toggleRole = async (member) => {
      const newRole = member.role === 'admin' ? 'member' : 'admin'
      try {
        console.log('Toggling role:', chatId, member.id, newRole)
        await chatsAPI.updateMemberRole(chatId, member.id, newRole)
        await loadChat()
      } catch (error) {
        console.error('Error updating role:', error)
        const msg = error.response?.data?.detail || error.message || 'Ошибка изменения роли'
        alert(msg)
      }
    }

    const removeMemberFromGroup = async (member) => {
      if (!confirm(`Удалить ${member.user?.full_name || member.user?.email} из группы?`)) return
      try {
        await chatsAPI.removeMember(chatId, member.id)
        await loadChat()
      } catch (error) {
        console.error('Error removing member:', error)
        alert('Ошибка удаления участника')
      }
    }

    const leaveGroup = async () => {
      if (!confirm('Вы уверены, что хотите покинуть группу?')) return
      try {
        await chatsAPI.leaveChat(chatId)
        router.push('/')
      } catch (error) {
        console.error('Error leaving group:', error)
        alert('Ошибка выхода из группы')
      }
    }

    const saveChatName = async () => {
      if (!editedName.value.trim()) {
        cancelEditName()
        return
      }
      try {
        const updatedChat = await chatsAPI.updateChatName(chatId, editedName.value.trim())
        chatName.value = updatedChat.name
        currentChat.value = updatedChat
        isEditingName.value = false
      } catch (err) {
        console.log('Full error object:', err)
        console.log('err.response:', err.response)
        console.log('err.response.status:', err.response?.status)
        console.log('err.response.data:', err.response?.data)
        
        let msg = 'Ошибка'
        if (err && typeof err === 'object') {
          if (err.response && err.response.data) {
            msg = `Status: ${err.response.status}, Data: ${JSON.stringify(err.response.data)}`
          } else if (err.request) {
            msg = 'Сервер не отвечает'
          } else {
            msg = err.message || JSON.stringify(err)
          }
        } else {
          msg = String(err)
        }
        alert(msg)
      }
    }

    const cancelEditName = () => {
      editedName.value = chatName.value
      isEditingName.value = false
    }

    const goBack = () => {
      router.push('/')
    }

    onMounted(async () => {
      try {
        const user = await authAPI.getCurrentUser()
        currentUserId.value = user.id
        currentUser.value = user  // Сохраняем полные данные пользователя
        await loadChat()
        await loadMessages()
        setupWebSocket()
        
        // Polling for new messages (fallback if WebSocket fails)
        pollInterval = setInterval(async () => {
          if (!ws.value || !ws.value.ws || ws.value.ws.readyState !== WebSocket.OPEN) {
            try {
              const response = await chatsAPI.getMessages(chatId)
              const newMessages = response.data || []
              const lastMsgId = messages.value.length > 0 ? Math.max(...messages.value.map(m => m.id)) : 0
              const unread = newMessages.filter(m => m.id > lastMsgId)
              if (unread.length > 0) {
                messages.value = [...messages.value, ...unread]
                scrollToBottom()
              }
            } catch (e) {}
          }
        }, 3000)
        
        // Дополнительная прокрутка после полной загрузки компонента
        await nextTick()
        setTimeout(() => {
          scrollToBottom(true)
        }, 500)
      } catch (error) {
        console.error('Error initializing chat:', error)
        router.push('/')
      }
    })

    onUnmounted(() => {
      if (ws.value) {
        ws.value.disconnect()
      }
      if (typingTimeout) clearTimeout(typingTimeout)
      if (pollInterval) clearInterval(pollInterval)
      if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
        mediaRecorder.value.stop()
      }
      stopRecordingTimer()
      endCall()
    })

    watch(() => route.params.chatId, async (newChatId) => {
      if (ws.value) {
        ws.value.disconnect()
      }
      loading.value = true
      messages.value = []
      shouldAutoScroll.value = true
      currentChat.value = null
      await loadChat()
      await loadMessages()
      setupWebSocket()
      // Дополнительная прокрутка после переключения чата
      await nextTick()
      setTimeout(() => {
        scrollToBottom(true)
      }, 500)
    })
    
    // Отслеживаем изменения в messages для автоматической прокрутки
    watch(messages, () => {
      if (shouldAutoScroll.value) {
        scrollToBottom()
      }
    }, { deep: true })

    watch(showsVideoStage, (visible) => {
      if (visible) {
        attachCallStreams()
      }
    })

    return {
      messages,
      loading,
      newMessage,
      chatName,
      currentUserId,
      currentUser,
      messagesContainer,
      isGroupChat,
      isBotChat,
      currentBot,
      isAdmin,
      isEditingName,
      editedName,
      showGroupMembers,
      showAddMembers,
      memberSearchQuery,
      memberSearchResults,
      membersToAdd,
      addingMembers,
      addMemberError,
      selectedFile,
      uploading,
      fileInput,
      showDrawingModal,
      drawingCanvas,
      drawingColor,
      drawingSize,
      currentChat,
      sendMessage,
      handleTyping,
      getSenderName,
      getSenderInitials,
      getSenderStyle,
      isSenderUltra,
      getAvatarClass,
      formatTime,
      handleFileSelect,
      clearFile,
      openDrawingModal,
      closeDrawingModal,
      startDrawing,
      drawOnCanvas,
      stopDrawing,
      clearDrawingCanvas,
      attachDrawing,
      handleMemberSearch,
      setupWebSocket,
      toggleAddMember,
      isAddMemberSelected,
      removeAddMember,
      addMembersToGroup,
      goBack,
deleteMessage,
      toggleRole,
      sendToAI,
      sendAIChat,
      showAIModal,
      aiEditText,
      aiEditPrompt,
      aiMode,
      aiResult,
      applyAIEdit,
      applyAIResult,
      removeMemberFromGroup,
      leaveGroup,
      saveChatName,
      cancelEditName,
      isUserOnline,
      onlineUsers,
      typingUser,
      isRecording,
      recordingTime,
      toggleVoiceRecording,
      startCall,
      acceptCall,
      declineCall,
      endCall,
      toggleMute,
      toggleCamera,
      inCall,
      callStatus,
      callMode,
      showsVideoStage,
      canToggleCamera,
      remoteUser,
      incomingCall,
      audioRef,
      localVideoRef,
      remoteVideoRef,
      isMuted,
      isCameraOn,
      getCallInitials,
      openMediaModal,
    }
  },
}
</script>

<style scoped>
.chat-container {
  max-width: 1200px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.back-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  color: var(--primary-purple-light);
}

.chat-header h2 {
  margin: 0;
  flex: 1;
  text-align: center;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  background: var(--bg-dark);
  pointer-events: none;
}

.chat-content > * {
  pointer-events: auto;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: var(--bg-dark);
}

.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: var(--bg-card);
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--primary-purple);
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--primary-purple-light);
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.875rem 1rem;
  background: var(--bg-card);
  border-radius: 12px;
  max-width: 70%;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--primary-purple);
}

.message-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
  border: 2px solid var(--primary-purple);
}

.message-avatar.avatar-gold,
.message-avatar-placeholder.avatar-gold {
  border: 3px solid #ffd700;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
}

.message-avatar.avatar-border,
.message-avatar-placeholder.avatar-border {
  border: 3px solid #9333ea;
  box-shadow: 0 0 10px rgba(147, 51, 234, 0.5);
}

.message-avatar.avatar-shine,
.message-avatar-placeholder.avatar-shine {
  position: relative;
}

.message-avatar.avatar-shine::after,
.message-avatar-placeholder.avatar-shine::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.3) 50%, transparent 60%);
  border-radius: 50%;
  pointer-events: none;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.avatar-wrapper .online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  background: #22c55e;
  border: 2px solid var(--bg-dark);
  border-radius: 50%;
}

.own-message .avatar-wrapper .online-indicator {
  border-color: var(--primary-purple);
}

.message-body {
  flex: 1;
  min-width: 0;
}

.own-message .message-avatar {
  border-color: rgba(255, 255, 255, 0.5);
}

.message:hover {
  border-color: var(--primary-purple);
}

.own-message {
  margin-left: auto;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.3);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.message-header strong {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.ultra-badge-small {
  font-size: 0.9rem;
}

.verified-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: bold;
  margin-left: 4px;
  vertical-align: middle;
}

.sender-name-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ultra-badge-small {
  font-size: 0.9rem;
}

.message-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.delete-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.25rem;
  opacity: 0.5;
  transition: all 0.3s ease;
  line-height: 1;
}

.delete-btn:hover {
  color: var(--error);
  opacity: 1;
}

.message-header strong {
  color: var(--text-primary);
  font-weight: 600;
}

.own-message .message-header strong {
  color: rgba(255, 255, 255, 0.95);
}

.message-time {
  opacity: 0.7;
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.own-message .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.message-content {
  word-wrap: break-word;
  color: var(--text-primary);
  line-height: 1.5;
}

.own-message .message-content {
  color: white;
}

.input-container {
  display: flex;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card);
  gap: 0.75rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
  align-items: center;
}

.typing-indicator {
  padding: 0.5rem 1rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-style: italic;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
}

.call-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.call-modal.incoming-call {
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
}

.call-info {
  text-align: center;
  color: white;
}

.call-content {
  text-align: center;
  color: white;
}

.call-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.call-status {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: var(--primary-purple-light);
}

.call-user {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 2rem;
}

.call-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}

.accept-btn {
  padding: 1rem 2rem;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.accept-btn:hover {
  transform: scale(1.05);
}

.decline-btn {
  padding: 1rem 2rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.decline-btn:hover {
  transform: scale(1.05);
}

.end-call-btn {
  padding: 1rem 2rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  cursor: pointer;
}

.call-btn {
  padding: 0.5rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

.call-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.input-container input {
  flex: 1;
  min-width: 0;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.input-container input::placeholder {
  color: var(--text-muted);
}

.input-container input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
  background: rgba(10, 10, 10, 0.7);
}

.input-container button {
  flex: 0 0 auto;
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.send-icon {
  display: none;
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
}

.input-container button:disabled {
  background: var(--bg-card-hover);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.5;
}

.voice-btn {
  padding: 0.5rem;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s ease;
}

.voice-btn:hover {
  background: var(--bg-card-hover);
}

.voice-btn.recording {
  background: #ef4444;
  border-color: #ef4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.recording-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  font-weight: 500;
}

.recording-dot {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.add-members-btn {
  padding: 0.5rem 1rem;
  background: rgba(147, 51, 234, 0.2);
  border: 1px solid var(--primary-purple);
  border-radius: 8px;
  cursor: pointer;
  color: var(--primary-purple-light);
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.add-members-btn:hover {
  background: rgba(147, 51, 234, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(147, 51, 234, 0.3);
}

/* Модальное окно (аналогично Home.vue) */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--bg-card);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(147, 51, 234, 0.3);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1001;
  position: relative;
  pointer-events: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 2rem;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
}

.modal-body .form-group {
  margin-bottom: 1.5rem;
}

.modal-body label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

.modal-body input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
  background: rgba(10, 10, 10, 0.5);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.modal-body input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
}

.member-search-results {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(10, 10, 10, 0.5);
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.3s ease;
  border-bottom: 1px solid var(--border-color);
}

.member-item:last-child {
  border-bottom: none;
}

.member-item:hover {
  background: var(--bg-card-hover);
}

.member-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.member-info strong {
  color: var(--text-primary);
  font-size: 0.9rem;
}

.member-email {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-color);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  font-weight: 700;
  transition: all 0.3s ease;
}

.checkbox.checked {
  background: var(--primary-purple);
  border-color: var(--primary-purple);
}

.selected-members {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.selected-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.member-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(147, 51, 234, 0.2);
  color: var(--primary-purple-light);
  border-radius: 6px;
  font-size: 0.875rem;
}

.remove-member {
  background: none;
  border: none;
  color: var(--primary-purple-light);
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.remove-member:hover {
  background: rgba(147, 51, 234, 0.3);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.cancel-btn,
.create-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.cancel-btn:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.create-btn {
  background: linear-gradient(135deg, var(--primary-purple) 0%, var(--primary-purple-light) 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.create-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.5);
}

.create-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.error {
  color: var(--error);
  margin-top: 0.5rem;
  font-size: 0.9rem;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.attach-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  flex: 0 0 44px;
}

.attach-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  color: var(--primary-purple-light);
}

.input-container .draw-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  transition: all 0.3s ease;
  flex: 0 0 44px;
}

.input-container .draw-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  color: var(--primary-purple-light);
}

.drawing-modal {
  max-width: 720px;
}

.drawing-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.drawing-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.drawing-control input[type="color"] {
  width: 52px;
  height: 40px;
  padding: 0.2rem;
  background: #ffffff;
  border: 1px solid rgba(124, 58, 237, 0.18);
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(124, 58, 237, 0.08);
}

.drawing-size-control {
  flex: 1 1 220px;
}

.drawing-size-control input[type="range"] {
  flex: 1;
  min-width: 140px;
  accent-color: var(--primary-purple);
}

.drawing-size-value {
  min-width: 2.4rem;
  padding: 0.35rem 0.55rem;
  color: var(--primary-purple-dark);
  text-align: right;
  border-radius: 999px;
  background: rgba(124, 58, 237, 0.1);
  font-weight: 600;
}

.drawing-action-btn {
  min-height: 2.75rem;
  padding: 0.72rem 1.1rem;
  border: 1px solid rgba(124, 58, 237, 0.14);
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: 0.01em;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.drawing-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px rgba(124, 58, 237, 0.12);
}

.drawing-clear-btn,
.drawing-cancel-btn {
  background: rgba(124, 58, 237, 0.08);
  color: var(--primary-purple-dark);
}

.drawing-clear-btn:hover,
.drawing-cancel-btn:hover {
  border-color: rgba(124, 58, 237, 0.24);
  background: rgba(124, 58, 237, 0.14);
}

.drawing-attach-btn {
  background: linear-gradient(135deg, var(--primary-purple), var(--primary-purple-light));
  color: #ffffff;
  box-shadow: 0 14px 28px rgba(124, 58, 237, 0.24);
}

.drawing-attach-btn:hover {
  border-color: rgba(124, 58, 237, 0.32);
}

.drawing-canvas {
  display: block;
  width: calc(100% - 3rem);
  height: 360px;
  margin: 1rem 1.5rem;
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  touch-action: none;
  cursor: crosshair;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: rgba(147, 51, 234, 0.1);
  border: 1px solid var(--primary-purple);
  border-radius: 8px;
  margin: 0.5rem 1.5rem;
}

.file-name {
  color: var(--text-primary);
  font-size: 0.9rem;
  word-break: break-all;
}

.clear-file {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 0.5rem;
  transition: color 0.3s ease;
}

.clear-file:hover {
  color: var(--error);
}

.message-media {
  margin-bottom: 0.5rem;
}

.media-image {
  max-width: 300px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.media-image:hover {
  transform: scale(1.02);
}

.media-audio audio {
  width: 100%;
  max-width: 300px;
  margin-top: 0.5rem;
}

.media-document {
  margin-top: 0.5rem;
}

.document-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  text-decoration: none;
  transition: all 0.3s ease;
}

.document-link:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.own-message .document-link {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.own-message .document-link:hover {
  background: rgba(255, 255, 255, 0.2);
}

.members-btn {
  padding: 0.5rem 1rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.3s ease;
}

.members-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
  color: var(--primary-purple-light);
}

.members-modal {
  max-width: 450px;
}

.members-list {
  max-height: 400px;
  overflow-y: auto;
}

.member-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.member-row:last-child {
  border-bottom: none;
}

.member-row .member-info {
  display: flex;
  flex-direction: column;
}

.member-row .member-info strong {
  color: var(--text-primary);
}

.member-role {
  font-size: 0.8rem;
  color: var(--primary-purple-light);
}

.member-actions {
  display: flex;
  gap: 0.5rem;
}

.role-btn {
  padding: 0.375rem 0.625rem;
  background: rgba(147, 51, 234, 0.2);
  border: 1px solid var(--primary-purple);
  border-radius: 6px;
  cursor: pointer;
  color: var(--primary-purple-light);
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.role-btn:hover {
  background: rgba(147, 51, 234, 0.3);
}

.remove-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0 0.25rem;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  color: var(--error);
  opacity: 1;
}

.leave-btn {
  width: 100%;
  padding: 0.875rem 1.5rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid var(--error);
  border-radius: 8px;
  cursor: pointer;
  color: var(--error);
  font-weight: 500;
  transition: all 0.3s ease;
}

.leave-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.chat-title {
  flex: 1;
  text-align: center;
  cursor: default;
}

.chat-title h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
  font-weight: 600;
}

.chat-title:hover h2 {
  color: var(--primary-purple-light);
}

.name-input {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--primary-purple);
  border-radius: 6px;
  font-size: 1.25rem;
  font-weight: 600;
  background: var(--bg-card);
  color: var(--text-primary);
  text-align: center;
  width: 200px;
}

.name-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.2);
}

.settings-btn {
  padding: 0.5rem;
  background: rgba(10, 10, 10, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.settings-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-purple);
}

.ai-btn {
  padding: 10px 16px;
  background: #9333ea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
}

.ai-btn:hover {
  background: #7c3aed;
}

@media (max-width: 640px) {
  .chat-container {
    height: 100dvh;
    max-width: none;
  }

  .chat-header {
    padding: 0.75rem;
    gap: 0.5rem;
  }

  .chat-title {
    min-width: 0;
    flex: 1;
  }

  .chat-header h2 {
    text-align: left;
    font-size: 1rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .back-btn {
    padding: 0.5rem 0.75rem;
    flex: 0 0 auto;
  }

  .messages-container {
    padding: 0.75rem;
  }

  .message {
    max-width: 92%;
    padding: 0.75rem;
  }

  .input-container {
    padding: 0.75rem;
    gap: 0.5rem;
  }

  .input-container input {
    font-size: 16px;
    padding: 0.75rem;
  }

  .input-container button,
  .attach-btn {
    width: 42px;
    height: 42px;
    min-width: 42px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .send-text {
    display: none;
  }

  .send-icon {
    display: inline;
    font-size: 1rem;
    line-height: 1;
  }
}

.ai-modal {
  max-width: 500px;
}

.ai-modal .btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary-purple) 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ai-modal .btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
}

.ai-modal .btn-secondary {
  padding: 12px 24px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ai-modal .btn-secondary:hover {
  border-color: var(--primary-purple);
  color: var(--text-primary);
}

.ai-modal .input {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.ai-modal .input:focus {
  outline: none;
  border-color: var(--primary-purple);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.2);
}

.ai-modal .input::placeholder {
  color: var(--text-secondary);
}

.ai-edit-mode .form-group {
  margin-bottom: 16px;
}

.ai-edit-mode label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.ai-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-template-btn {
  padding: 8px 16px;
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.ai-template-btn:hover {
  border-color: var(--primary-purple);
}

.ai-template-btn.active {
  background: var(--primary-purple);
  color: white;
  border-color: var(--primary-purple);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.ai-chat-mode {
  padding: 20px;
  text-align: center;
}

.ai-hint {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

/* Telegram-like chat polish */
.chat-container {
  max-width: none;
  --chat-page-bg:
    radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary-purple) 10%, transparent), transparent 28%),
    var(--page-gradient);
  --chat-header-bg: color-mix(in srgb, var(--bg-card) 92%, transparent);
  --chat-header-border: var(--border-color);
  --chat-action-color: var(--text-secondary);
  --chat-action-hover-bg: var(--bg-card-hover);
  --chat-title-color: var(--text-primary);
  --chat-thread-bg:
    linear-gradient(color-mix(in srgb, var(--bg-card) 24%, transparent), color-mix(in srgb, var(--bg-card) 24%, transparent)),
    repeating-linear-gradient(135deg, color-mix(in srgb, var(--primary-purple) 8%, transparent) 0 2px, transparent 2px 34px),
    var(--bg-dark);
  --chat-bubble-bg: var(--bg-card);
  --chat-own-bubble-bg: color-mix(in srgb, var(--success) 18%, var(--bg-card));
  --chat-bubble-shadow: var(--shadow-soft);
  --chat-message-text: var(--text-primary);
  --chat-sender-color: var(--primary-purple-dark);
  --chat-own-sender-color: var(--success);
  --chat-meta-color: var(--text-muted);
  --chat-input-bg: var(--bg-input);
  --chat-panel-bg: color-mix(in srgb, var(--bg-card) 90%, transparent);
  --chat-soft-control-bg: var(--bg-card);
  background: var(--chat-page-bg);
}

:global([data-theme='dark']) .chat-container {
  --chat-bubble-shadow: 0 1px 2px rgba(0, 0, 0, 0.34);
  --chat-own-bubble-bg: color-mix(in srgb, var(--success) 20%, var(--bg-elevated));
}

.chat-header {
  height: 64px;
  padding: 0.625rem 1rem;
  background: var(--chat-header-bg);
  border-bottom: 1px solid var(--chat-header-border);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px);
}

.back-btn,
.members-btn,
.settings-btn,
.call-btn,
.add-members-btn {
  width: 42px;
  height: 42px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--chat-action-color);
  box-shadow: none;
}

.back-btn {
  font-size: 2rem;
  line-height: 1;
}

.call-btn,
.members-btn,
.settings-btn {
  font-size: 1.2rem;
}

.back-btn:hover,
.members-btn:hover,
.settings-btn:hover,
.call-btn:hover,
.add-members-btn:hover {
  background: var(--chat-action-hover-bg);
  color: var(--primary-purple-dark);
  transform: none;
  box-shadow: none;
}

.chat-title {
  min-width: 0;
}

.chat-title h2 {
  max-width: 44vw;
  margin: 0 auto;
  color: var(--chat-title-color);
  font-size: 1.05rem;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  gap: 0.25rem;
}

.chat-content,
.messages-container {
  background: var(--chat-thread-bg);
}

.messages-container {
  padding: 1rem max(1rem, calc((100vw - 920px) / 2));
}

.message {
  position: relative;
  max-width: min(680px, 74%);
  margin-bottom: 0.45rem;
  padding: 0;
  gap: 0.5rem;
  background: transparent;
  border: none;
  box-shadow: none;
}

.message:hover {
  border-color: transparent;
}

.message-body {
  width: fit-content;
  max-width: 100%;
  padding: 0.45rem 0.7rem 0.38rem;
  background: var(--chat-bubble-bg);
  border-radius: 8px 18px 18px 18px;
  box-shadow: var(--chat-bubble-shadow);
}

.own-message .message-body {
  margin-left: auto;
  background: var(--chat-own-bubble-bg);
  border-radius: 18px 8px 18px 18px;
}

.own-message {
  background: transparent;
  box-shadow: none;
}

.message-avatar,
.message-avatar-placeholder {
  width: 34px;
  height: 34px;
  border: none;
  box-shadow: var(--chat-bubble-shadow);
}

.message-avatar-placeholder {
  background: linear-gradient(135deg, #2ca5dc, #7acb8f);
  font-size: 0.78rem;
}

.message-header {
  gap: 0.75rem;
  margin-bottom: 0.18rem;
  line-height: 1.2;
}

.message-header strong {
  color: var(--chat-sender-color);
  font-size: 0.82rem;
}

.own-message .message-header strong {
  color: var(--chat-own-sender-color);
}

.message-content {
  color: var(--chat-message-text);
  font-size: 0.96rem;
  line-height: 1.35;
  white-space: pre-wrap;
}

.own-message .message-content {
  color: var(--chat-message-text);
}

.message-time,
.own-message .message-time,
.read-status {
  color: var(--chat-meta-color);
  font-size: 0.7rem;
  opacity: 1;
}

.read-status {
  color: #2196d3;
}

.delete-btn {
  width: 20px;
  height: 20px;
  color: #7d94a4;
  border-radius: 50%;
}

.delete-btn:hover {
  background: rgba(222, 62, 62, 0.12);
}

.input-container {
  margin: 0 auto;
  width: min(960px, 100%);
  padding: 0.65rem 0.8rem 0.8rem;
  background: transparent;
  border-top: none;
  box-shadow: none;
}

.input-container input {
  min-height: 46px;
  border: none;
  border-radius: 23px;
  padding: 0 1rem;
  background: var(--chat-input-bg);
  color: var(--text-primary);
  box-shadow: var(--chat-bubble-shadow);
}

.input-container input:focus {
  border-color: transparent;
  background: var(--chat-input-bg);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary-purple) 25%, transparent), var(--chat-bubble-shadow);
}

.attach-btn,
.input-container .draw-btn,
.input-container .voice-btn,
.input-container .ai-btn,
.input-container .send-btn {
  width: 46px;
  height: 46px;
  min-width: 46px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--chat-soft-control-bg);
  color: var(--text-secondary);
  box-shadow: var(--chat-bubble-shadow);
}

.input-container .send-btn {
  background: var(--primary-purple);
  color: #ffffff;
}

.input-container .voice-btn.recording {
  background: #e84f4f;
  color: #ffffff;
  animation: none;
}

.attach-btn:hover,
.input-container .draw-btn:hover,
.input-container .voice-btn:hover,
.input-container .ai-btn:hover,
.input-container .send-btn:hover:not(:disabled) {
  transform: none;
  background: #f2ebff;
  color: var(--primary-purple-dark);
  box-shadow: 0 1px 4px rgba(49, 28, 86, 0.18);
}

.input-container .send-btn:hover:not(:disabled) {
  background: var(--primary-purple-dark);
  color: #ffffff;
}

.input-container .send-btn:disabled {
  background: #d9cdf1;
  color: #ffffff;
  opacity: 1;
}

.send-text {
  display: none;
}

.send-icon {
  display: inline;
}

.file-preview,
.recording-indicator,
.typing-indicator {
  width: min(936px, calc(100% - 1.6rem));
  margin: 0.2rem auto 0;
  border: none;
  border-radius: 18px;
  background: var(--chat-panel-bg);
  color: var(--text-secondary);
  box-shadow: var(--chat-bubble-shadow);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0.35rem 1rem;
  font-style: normal;
}

.typing-indicator i {
  width: 4px;
  height: 4px;
  background: #8f7ab8;
  border-radius: 50%;
  animation: typingDot 1.2s infinite ease-in-out;
}

.typing-indicator i:nth-child(3) {
  animation-delay: 0.15s;
}

.typing-indicator i:nth-child(4) {
  animation-delay: 0.3s;
}

@keyframes typingDot {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.45; }
  40% { transform: translateY(-3px); opacity: 1; }
}

.message-media {
  overflow: hidden;
  margin: -0.12rem -0.38rem 0.38rem;
}

.media-image {
  display: block;
  width: min(360px, 62vw);
  max-width: 100%;
  max-height: 360px;
  border-radius: 14px;
  object-fit: cover;
}

.media-audio {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-width: min(330px, 64vw);
  padding: 0.35rem 0.25rem;
}

.media-audio audio {
  max-width: none;
  width: 100%;
  height: 34px;
  margin: 0;
}

.voice-wave {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--primary-purple);
}

.voice-wave i {
  width: 3px;
  border-radius: 3px;
  background: currentColor;
}

.voice-wave i:nth-child(1) { height: 12px; }
.voice-wave i:nth-child(2) { height: 20px; }
.voice-wave i:nth-child(3) { height: 15px; }
.voice-wave i:nth-child(4) { height: 25px; }
.voice-wave i:nth-child(5) { height: 10px; }

.document-link {
  border: none;
  border-radius: 14px;
  background: #f3ecff;
  color: #342257;
}

.own-message .document-link {
  background: rgba(255, 255, 255, 0.45);
  color: #342257;
}

.modal-content {
  border-radius: 14px;
  background: #ffffff;
  color: #10202e;
  border: 1px solid #e2d6fb;
  box-shadow: 0 20px 70px rgba(71, 38, 129, 0.18);
}

.drawing-modal {
  max-width: 760px;
}

.drawing-toolbar {
  background:
    linear-gradient(180deg, rgba(246, 241, 255, 0.95), rgba(255, 255, 255, 0.96));
  border-top-left-radius: 14px;
  border-top-right-radius: 14px;
}

.drawing-canvas {
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px #e5d7ff;
}

.call-modal {
  background:
    radial-gradient(circle at 50% 20%, rgba(167, 139, 250, 0.45), transparent 35%),
    linear-gradient(160deg, #2d1148 0%, #140624 100%);
  backdrop-filter: blur(12px);
}

.call-content,
.call-panel {
  width: min(420px, calc(100vw - 2rem));
  min-height: 420px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  text-align: center;
}

.call-avatar {
  width: 112px;
  height: 112px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.2rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #c084fc);
  color: white;
  font-size: 2.4rem;
  font-weight: 800;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

.call-user {
  margin-bottom: 0.4rem;
  font-size: 1.45rem;
}

.call-status {
  color: rgba(255, 255, 255, 0.76);
}

.call-actions,
.call-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
  align-items: center;
  margin-top: 2rem;
}

.accept-btn,
.decline-btn,
.end-call-btn,
.call-control-btn {
  width: 58px;
  height: 58px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
}

.accept-btn {
  background: #26c46f;
}

.decline-btn,
.end-call-btn {
  background: #e34b4b;
}

.call-control-btn {
  background: rgba(255,255,255,0.18);
  backdrop-filter: blur(8px);
}

.call-control-btn.active {
  background: rgba(255, 255, 255, 0.34);
}

.video-stage {
  position: relative;
  width: min(860px, calc(100vw - 2rem));
  height: min(620px, calc(100vh - 9rem));
  min-height: 420px;
  overflow: hidden;
  border-radius: 18px;
  background: #05131e;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
}

.call-panel.video-call {
  width: auto;
  min-height: auto;
  padding: 1rem;
}

.remote-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #071d2d;
}

.local-video {
  position: absolute;
  right: 1rem;
  bottom: 1rem;
  width: min(190px, 32vw);
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border: 2px solid rgba(255,255,255,0.8);
  border-radius: 14px;
  background: #10202e;
  box-shadow: 0 8px 26px rgba(0,0,0,0.32);
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.7);
  font-size: 1.4rem;
  pointer-events: none;
}

.call-panel.video-call .call-controls {
  position: fixed;
  left: 50%;
  bottom: 2rem;
  transform: translateX(-50%);
  margin: 0;
  padding: 0.55rem;
  border-radius: 999px;
  background: rgba(6, 23, 36, 0.55);
  backdrop-filter: blur(14px);
}

@media (max-width: 640px) {
  .chat-header {
    height: 58px;
  }

  .chat-title h2 {
    max-width: 38vw;
  }

  .message {
    max-width: 88%;
  }

  .avatar-wrapper {
    display: none;
  }

  .messages-container {
    padding: 0.75rem;
  }

  .input-container {
    padding: 0.55rem;
  }

  .input-container .ai-btn {
    display: none;
  }

  .media-image {
    width: min(300px, 72vw);
  }

  .call-content,
  .call-panel {
    min-height: 360px;
  }

  .video-stage {
    width: calc(100vw - 1rem);
    height: calc(100vh - 8rem);
    min-height: 360px;
  }
}
</style>
