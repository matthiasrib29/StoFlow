<template>
  <section class="hero-section">
    <div class="hero-container">
      <div class="hero-content">
        <h1 class="hero-title">
          Publiez sur Vinted & eBay en <span class="highlight">10 secondes</span> avec l'IA
        </h1>

        <p class="hero-subtitle">
          Arrêtez de recopier 10x les mêmes descriptions. Stoflow génère et publie automatiquement.
        </p>

        <div class="hero-cta">
          <LandingSignupForm :show-full-form="false" />

          <div class="places-counter">
            <span class="counter-icon">⏰</span>
            <span class="counter-text">Plus que <strong>{{ placesRestantes }}/50</strong> places</span>
          </div>
        </div>

        <div class="hero-benefits">
          <div class="benefit">
            <span class="benefit-icon">✅</span>
            <span>Gratuit 1 mois</span>
          </div>
          <div class="benefit">
            <span class="benefit-icon">✅</span>
            <span>-50% à vie</span>
          </div>
          <div class="benefit">
            <span class="benefit-icon">✅</span>
            <span>Sans engagement</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const placesRestantes = inject<Ref<number>>('placesRestantes')!
</script>

<style scoped>
.hero-section {
  min-height: 90vh;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
  padding: 4rem 1.5rem;
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.hero-content {
  text-align: center;
  color: white;
}

.hero-title {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1.5rem;
}

.highlight {
  color: #facc15;
}

.hero-subtitle {
  font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  color: #d1d5db;
  margin-bottom: 3rem;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.hero-cta {
  margin-bottom: 2rem;
}

.places-counter {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: rgba(250, 204, 21, 0.1);
  border: 1px solid #facc15;
  border-radius: 9999px;
  font-size: 0.95rem;
}

.counter-icon {
  font-size: 1.2rem;
}

.counter-text strong {
  color: #facc15;
  font-weight: 700;
}

.hero-benefits {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
  margin-top: 3rem;
}

.benefit {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.benefit-icon {
  font-size: 1.2rem;
}

@media (max-width: 768px) {
  .hero-section {
    min-height: auto;
    padding: 3rem 1rem;
  }

  .hero-benefits {
    gap: 1rem;
  }

  .benefit {
    font-size: 0.9rem;
  }
}
</style>
