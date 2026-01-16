<template>
  <section class="howitworks-section">
    <div class="section-container">
      <h2 class="section-title">⚡ Comment Stoflow vous fait gagner 90% de temps</h2>

      <div class="steps-container">
        <div v-for="(step, index) in steps" :key="index" class="step-card">
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-icon">{{ step.icon }}</div>
          <h3 class="step-title">{{ step.title }}</h3>
          <p class="step-description">{{ step.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const steps = [
  {
    icon: '📸',
    title: 'Upload photo',
    description: 'Déposez votre photo ou prenez-la directement depuis l\'app'
  },
  {
    icon: '🤖',
    title: 'IA génère description',
    description: 'Notre IA analyse l\'image et crée une description optimisée'
  },
  {
    icon: '🚀',
    title: 'Publie automatiquement',
    description: 'Un clic et c\'est publié sur Vinted, eBay, Etsy simultanément'
  }
]
</script>

<style scoped>
.howitworks-section {
  padding: 5rem 1.5rem;
  background: white;
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 700;
  text-align: center;
  margin-bottom: 4rem;
  color: #1a1a1a;
}

.steps-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 3rem;
  margin-bottom: 4rem;
}

.step-card {
  text-align: center;
  position: relative;
}

.step-number {
  position: absolute;
  top: -1rem;
  left: 50%;
  transform: translateX(-50%);
  width: 2.5rem;
  height: 2.5rem;
  background: #facc15;
  color: #1a1a1a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.25rem;
}

.step-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.step-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1a1a1a;
}

.step-description {
  color: #6b7280;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .howitworks-section {
    padding: 3rem 1rem;
  }

  .steps-container {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
