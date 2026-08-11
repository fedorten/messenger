<template>
  <span class="user-name">
    <span class="user-name-text">{{ displayName }}</span>
    <span v-if="user && user.is_verified" class="verified-check" title="Верифицирован">✓</span>
    <span v-if="user && user.is_ultra" class="ultra-check" title="Ultra">{{ user.ultra_badge || '⚡' }}</span>
  </span>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'UserName',
  props: {
    user: { type: Object, default: null },
    fallback: { type: String, default: 'Пользователь' },
  },
  setup(props) {
    const displayName = computed(
      () => props.user?.full_name || props.user?.name || props.user?.email || props.fallback
    )
    return { displayName }
  },
}
</script>

<style scoped>
.user-name {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.user-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.verified-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--success);
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 700;
  flex-shrink: 0;
}

.ultra-check {
  color: var(--warning);
  font-size: 0.8rem;
  flex-shrink: 0;
}
</style>
