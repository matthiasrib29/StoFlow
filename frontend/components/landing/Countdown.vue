<template>
  <div class="countdown-wrapper">
    <div class="countdown-container">
      <div class="countdown-header">
        <span class="countdown-icon">🚀</span>
        <h3 class="countdown-title">Beta disponible dans</h3>
      </div>

      <div class="countdown-timer">
        <div class="time-unit">
          <div class="time-value">{{ days }}</div>
          <div class="time-label">jours</div>
        </div>
        <div class="time-separator">:</div>
        <div class="time-unit">
          <div class="time-value">{{ hours }}</div>
          <div class="time-label">heures</div>
        </div>
        <div class="time-separator">:</div>
        <div class="time-unit">
          <div class="time-value">{{ minutes }}</div>
          <div class="time-label">min</div>
        </div>
        <div class="time-separator">:</div>
        <div class="time-unit">
          <div class="time-value">{{ seconds }}</div>
          <div class="time-label">sec</div>
        </div>
      </div>

      <p class="countdown-deadline">Lancement le 14 février 2026</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const days = ref(0)
const hours = ref(0)
const minutes = ref(0)
const seconds = ref(0)

let intervalId: NodeJS.Timeout | null = null

const updateCountdown = () => {
  const now = new Date()
  const deadline = new Date('2026-02-14T23:59:59')
  const diff = deadline.getTime() - now.getTime()

  if (diff <= 0) {
    days.value = 0
    hours.value = 0
    minutes.value = 0
    seconds.value = 0
    if (intervalId) clearInterval(intervalId)
    return
  }

  days.value = Math.floor(diff / (1000 * 60 * 60 * 24))
  hours.value = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  minutes.value = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  seconds.value = Math.floor((diff % (1000 * 60)) / 1000)
}

onMounted(() => {
  updateCountdown()
  intervalId = setInterval(updateCountdown, 1000)
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
.countdown-wrapper {
  padding: 3rem 1.5rem;
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
}

.countdown-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.countdown-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.countdown-icon {
  font-size: 2rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.countdown-title {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  color: #facc15;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.countdown-timer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.time-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(250, 204, 21, 0.1);
  border: 2px solid #facc15;
  border-radius: 0.75rem;
  padding: 1.5rem 1rem;
  min-width: 100px;
}

.time-value {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
  font-weight: 800;
  color: #facc15;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.time-label {
  font-size: 0.875rem;
  color: #d1d5db;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.5rem;
}

.time-separator {
  font-size: 3rem;
  font-weight: 700;
  color: #facc15;
  line-height: 1;
}

.countdown-deadline {
  font-size: 1rem;
  color: #d1d5db;
  font-weight: 500;
}

@media (max-width: 768px) {
  .countdown-wrapper {
    padding: 2rem 1rem;
  }

  .countdown-header {
    margin-bottom: 1.5rem;
  }

  .countdown-icon {
    font-size: 1.5rem;
  }

  .countdown-title {
    font-size: 1.25rem;
  }

  .countdown-timer {
    gap: 0.5rem;
  }

  .time-unit {
    padding: 1rem 0.5rem;
    min-width: 70px;
  }

  .time-value {
    font-size: 2rem;
  }

  .time-label {
    font-size: 0.75rem;
  }

  .time-separator {
    font-size: 2rem;
  }

  .countdown-deadline {
    font-size: 0.875rem;
  }
}
</style>
