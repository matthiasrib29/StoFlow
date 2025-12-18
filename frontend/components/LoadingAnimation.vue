<template>
  <div :class="['loading-animation', sizeClass, variantClass]">
    <!-- Spinner par défaut -->
    <div v-if="type === 'spinner'" class="spinner-container">
      <div class="spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
      </div>
    </div>

    <!-- Dots animation -->
    <div v-else-if="type === 'dots'" class="dots-container">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>

    <!-- Pulse animation -->
    <div v-else-if="type === 'pulse'" class="pulse-container">
      <div class="pulse-ring"></div>
      <div class="pulse-center"></div>
    </div>

    <!-- Bars animation -->
    <div v-else-if="type === 'bars'" class="bars-container">
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
      <div class="bar"></div>
    </div>

    <!-- Box flip animation -->
    <div v-else-if="type === 'box'" class="box-container">
      <div class="box"></div>
    </div>

    <!-- Stoflow branded loader -->
    <div v-else-if="type === 'stoflow'" class="stoflow-loader">
      <div class="stoflow-box">
        <div class="box-face front"></div>
        <div class="box-face back"></div>
        <div class="box-face top"></div>
        <div class="box-face bottom"></div>
        <div class="box-face left"></div>
        <div class="box-face right"></div>
      </div>
    </div>

    <!-- Message -->
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  /** Type d'animation */
  type?: 'spinner' | 'dots' | 'pulse' | 'bars' | 'box' | 'stoflow'
  /** Taille */
  size?: 'small' | 'medium' | 'large'
  /** Variante de couleur */
  variant?: 'primary' | 'secondary' | 'white'
  /** Message à afficher */
  message?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'spinner',
  size: 'medium',
  variant: 'primary'
})

const sizeClass = computed(() => `loading-animation--${props.size}`)
const variantClass = computed(() => `loading-animation--${props.variant}`)
</script>

<style scoped>
.loading-animation {
  @apply flex flex-col items-center justify-center gap-3;
}

/* Sizes */
.loading-animation--small { --size: 24px; --font-size: 0.75rem; }
.loading-animation--medium { --size: 40px; --font-size: 0.875rem; }
.loading-animation--large { --size: 64px; --font-size: 1rem; }

/* Variants */
.loading-animation--primary { --color: var(--primary-400); }
.loading-animation--secondary { --color: var(--secondary-900); }
.loading-animation--white { --color: #ffffff; }

.loading-message {
  @apply text-center;
  font-size: var(--font-size);
  color: var(--color);
}

/* === SPINNER === */
.spinner-container {
  width: var(--size);
  height: var(--size);
}

.spinner {
  position: relative;
  width: 100%;
  height: 100%;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: var(--color);
  animation: spin 1s ease-in-out infinite;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  animation-delay: 0.15s;
  border-top-color: color-mix(in srgb, var(--color) 70%, transparent);
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  animation-delay: 0.3s;
  border-top-color: color-mix(in srgb, var(--color) 40%, transparent);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* === DOTS === */
.dots-container {
  display: flex;
  gap: calc(var(--size) / 5);
}

.dot {
  width: calc(var(--size) / 3);
  height: calc(var(--size) / 3);
  border-radius: 50%;
  background-color: var(--color);
  animation: dot-bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* === PULSE === */
.pulse-container {
  position: relative;
  width: var(--size);
  height: var(--size);
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid var(--color);
  animation: pulse-ring 1.5s ease-out infinite;
}

.pulse-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 30%;
  height: 30%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background-color: var(--color);
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.5);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

/* === BARS === */
.bars-container {
  display: flex;
  align-items: flex-end;
  gap: calc(var(--size) / 10);
  height: var(--size);
}

.bar {
  width: calc(var(--size) / 6);
  background-color: var(--color);
  border-radius: 2px;
  animation: bar-grow 1s ease-in-out infinite;
}

.bar:nth-child(1) { animation-delay: 0s; }
.bar:nth-child(2) { animation-delay: 0.1s; }
.bar:nth-child(3) { animation-delay: 0.2s; }
.bar:nth-child(4) { animation-delay: 0.3s; }
.bar:nth-child(5) { animation-delay: 0.4s; }

@keyframes bar-grow {
  0%, 100% { height: 30%; }
  50% { height: 100%; }
}

/* === BOX === */
.box-container {
  width: var(--size);
  height: var(--size);
  perspective: 100px;
}

.box {
  width: 100%;
  height: 100%;
  background-color: var(--color);
  border-radius: 4px;
  animation: box-flip 1.2s ease-in-out infinite;
}

@keyframes box-flip {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  25% { transform: rotateX(180deg) rotateY(0deg); }
  50% { transform: rotateX(180deg) rotateY(180deg); }
  75% { transform: rotateX(0deg) rotateY(180deg); }
  100% { transform: rotateX(0deg) rotateY(360deg); }
}

/* === STOFLOW BRANDED === */
.stoflow-loader {
  width: var(--size);
  height: var(--size);
  perspective: calc(var(--size) * 2);
}

.stoflow-box {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  animation: stoflow-rotate 2s ease-in-out infinite;
}

.box-face {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid var(--color);
  background: linear-gradient(135deg, var(--color), transparent);
  opacity: 0.8;
}

.box-face.front { transform: translateZ(calc(var(--size) / 2)); }
.box-face.back { transform: rotateY(180deg) translateZ(calc(var(--size) / 2)); }
.box-face.top { transform: rotateX(90deg) translateZ(calc(var(--size) / 2)); }
.box-face.bottom { transform: rotateX(-90deg) translateZ(calc(var(--size) / 2)); }
.box-face.left { transform: rotateY(-90deg) translateZ(calc(var(--size) / 2)); }
.box-face.right { transform: rotateY(90deg) translateZ(calc(var(--size) / 2)); }

@keyframes stoflow-rotate {
  0% { transform: rotateX(0deg) rotateY(0deg); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}
</style>
