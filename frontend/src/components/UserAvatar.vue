<template>
  <span class="user-avatar" :style="{ width: size + 'px', height: size + 'px' }">
    <img v-if="user && user.avatar_url" :src="user.avatar_url" :alt="displayName" class="user-avatar-img" />
    <span v-else class="user-avatar-initials" :style="{ fontSize: Math.round(size / 2.6) + 'px' }">
      {{ initials }}
    </span>
    <span
      v-if="showVerified && user && user.is_verified"
      class="user-avatar-verified"
      :style="{ width: badgeSize + 'px', height: badgeSize + 'px', fontSize: Math.round(badgeSize * 0.7) + 'px' }"
      title="Верифицирован"
    >✓</span>
  </span>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'UserAvatar',
  props: {
    user: { type: Object, default: null },
    size: { type: Number, default: 40 },
    showVerified: { type: Boolean, default: true },
  },
  setup(props) {
    const displayName = computed(
      () => props.user?.full_name || props.user?.name || props.user?.email || 'Пользователь'
    )

    const initials = computed(() => {
      const name = props.user?.full_name || props.user?.name || props.user?.email
      if (!name) return '?'
      return name
        .split(/[\s@._-]+/)
        .filter(Boolean)
        .map((part) => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    })

    const badgeSize = computed(() => Math.max(14, Math.round(props.size * 0.38)))

    return { displayName, initials, badgeSize }
  },
}
</script>

<style scoped>
.user-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: visible;
  background: linear-gradient(135deg, var(--primary-purple), var(--primary-purple-light));
  color: #ffffff;
  font-weight: 700;
}

.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-initials {
  line-height: 1;
}

.user-avatar-verified {
  position: absolute;
  right: -2px;
  bottom: -2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--success);
  color: #ffffff;
  border: 2px solid var(--bg-card);
  font-weight: 700;
  line-height: 1;
}
</style>
