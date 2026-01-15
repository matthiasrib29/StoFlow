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

      <div class="time-comparison">
        <div class="comparison-item old">
          <div class="comparison-label">AVANT</div>
          <div class="comparison-value">20 minutes</div>
        </div>

        <div class="comparison-arrow">→</div>

        <div class="comparison-item new">
          <div class="comparison-label">AVEC STOFLOW</div>
          <div class="comparison-value">10 secondes</div>
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

.time-comparison {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
  padding: 3rem;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 1rem;
}

.comparison-item {
  text-align: center;
  padding: 2rem;
  border-radius: 0.75rem;
  min-width: 200px;
}

.comparison-item.old {
  background: #fee2e2;
  border: 2px solid #ef4444;
}

.comparison-item.new {
  background: #dcfce7;
  border: 2px solid #22c55e;
}

.comparison-label {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  color: #6b7280;
}

.comparison-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a1a;
}

.comparison-arrow {
  font-size: 2rem;
  color: #facc15;
  font-weight: 700;
}

@media (max-width: 768px) {
  .howitworks-section {
    padding: 3rem 1rem;
  }

  .steps-container {
    grid-template-columns: 1fr;
    gap: 3rem;
  }

  .time-comparison {
    gap: 1rem;
    padding: 2rem 1rem;
  }

  .comparison-arrow {
    transform: rotate(90deg);
  }
}
</style>
