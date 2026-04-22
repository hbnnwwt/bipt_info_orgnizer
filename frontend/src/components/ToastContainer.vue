<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="'toast-' + toast.type"
        >
          <span class="toast-icon">{{ toastIcon(toast.type) }}</span>
          <span class="toast-msg">{{ toast.message }}</span>
          <button class="toast-close" @click="remove(toast.id)">×</button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { useToast } from '../composables/toast'

const { toasts, remove } = useToast()

function toastIcon(type) {
  return type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: var(--font-sans);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: all;
  max-width: 360px;
}

.toast-success {
  background: var(--toast-success-bg, #f0fdf4);
  color: var(--toast-success-text, #166534);
  border: 1px solid var(--toast-success-border, #bbf7d0);
}

.toast-error {
  background: var(--toast-error-bg, #fef2f2);
  color: var(--toast-error-text, #991b1b);
  border: 1px solid var(--toast-error-border, #fecaca);
}

.toast-info {
  background: var(--toast-info-bg, #f0f9ff);
  color: var(--toast-info-text, #0c4a6e);
  border: 1px solid var(--toast-info-border, #bae6fd);
}

.toast-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
}

.toast-msg {
  flex: 1;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  opacity: 0.5;
  padding: 0 0.25rem;
  color: inherit;
  flex-shrink: 0;
}

.toast-close:hover {
  opacity: 1;
}

/* Transition */
.toast-enter-active,
.toast-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(1rem);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
