<template>
  <button
    @click="themeStore.toggle()"
    class="theme-toggle"
    :class="{ 'is-dark': themeStore.isDark }"
    :aria-label="themeStore.isDark ? 'Activer le mode clair' : 'Activer le mode sombre'"
    :title="themeStore.isDark ? 'Mode clair' : 'Mode sombre'"
  >
    <div class="toggle-track">
      <!-- Soleil -->
      <div class="sun-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      </div>

      <!-- Lune -->
      <div class="moon-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </div>

      <!-- Toggle ball -->
      <div class="toggle-ball">
        <div class="ball-inner"></div>
      </div>
    </div>
  </button>
</template>

<script setup lang="ts">
const themeStore = useThemeStore()

// Charger le thème au montage
onMounted(() => {
  themeStore.loadFromStorage()
})
</script>

<style scoped>
.theme-toggle {
  @apply relative w-14 h-8 rounded-full cursor-pointer transition-all duration-300;
  background: linear-gradient(135deg, #87CEEB 0%, #E0F7FA 100%);
  padding: 2px;
}

.theme-toggle.is-dark {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.toggle-track {
  @apply relative w-full h-full rounded-full overflow-hidden;
}

/* Icons container */
.sun-icon,
.moon-icon {
  @apply absolute top-1/2 -translate-y-1/2 w-5 h-5 transition-all duration-300;
}

.sun-icon {
  @apply left-1.5;
  color: #f59e0b;
}

.moon-icon {
  @apply right-1.5;
  color: #fcd34d;
}

/* Hide/show icons based on state */
.theme-toggle .sun-icon {
  opacity: 1;
  transform: translateY(-50%) rotate(0deg) scale(1);
}

.theme-toggle .moon-icon {
  opacity: 0;
  transform: translateY(-50%) rotate(-90deg) scale(0.5);
}

.theme-toggle.is-dark .sun-icon {
  opacity: 0;
  transform: translateY(-50%) rotate(90deg) scale(0.5);
}

.theme-toggle.is-dark .moon-icon {
  opacity: 1;
  transform: translateY(-50%) rotate(0deg) scale(1);
}

/* Toggle ball */
.toggle-ball {
  @apply absolute top-1/2 -translate-y-1/2 w-6 h-6 rounded-full transition-all duration-300;
  left: 2px;
  background: linear-gradient(135deg, #fef3c7 0%, #fcd34d 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.theme-toggle.is-dark .toggle-ball {
  left: calc(100% - 26px);
  background: linear-gradient(135deg, #e5e7eb 0%, #9ca3af 100%);
}

.ball-inner {
  @apply w-full h-full rounded-full transition-all duration-300;
}

/* Craters on moon (dark mode) */
.theme-toggle.is-dark .ball-inner::before,
.theme-toggle.is-dark .ball-inner::after {
  content: '';
  @apply absolute rounded-full bg-gray-400/50;
}

.theme-toggle.is-dark .ball-inner::before {
  width: 6px;
  height: 6px;
  top: 4px;
  left: 4px;
}

.theme-toggle.is-dark .ball-inner::after {
  width: 4px;
  height: 4px;
  bottom: 6px;
  right: 6px;
}

/* Hover effect */
.theme-toggle:hover .toggle-ball {
  transform: translateY(-50%) scale(1.1);
}

.theme-toggle:active .toggle-ball {
  transform: translateY(-50%) scale(0.95);
}

/* Stars animation in dark mode */
.theme-toggle.is-dark::before,
.theme-toggle.is-dark::after {
  content: '';
  @apply absolute rounded-full bg-white/80;
  animation: twinkle 1.5s ease-in-out infinite;
}

.theme-toggle.is-dark::before {
  width: 2px;
  height: 2px;
  top: 8px;
  left: 8px;
}

.theme-toggle.is-dark::after {
  width: 1px;
  height: 1px;
  top: 14px;
  left: 14px;
  animation-delay: 0.5s;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.5); }
}
</style>
