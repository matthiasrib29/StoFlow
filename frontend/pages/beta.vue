<template>
  <div class="beta-page">
    <!-- Hero Section -->
    <LandingHero />

    <!-- Countdown Section -->
    <LandingCountdown />

    <!-- Problem Section -->
    <LandingProblem />

    <!-- CTA #2 -->
    <section class="cta-section-2">
      <div class="cta-container">
        <h3 class="cta-title">Prêt à gagner 90% de temps ?</h3>
        <LandingSignupForm :show-full-form="true" />
        <div class="places-counter">
          <span class="counter-icon">⏰</span>
          <span class="counter-text">Plus que <strong>{{ placesRestantes }}/100</strong> places</span>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <LandingHowItWorks />

    <!-- Features Section -->
    <LandingFeatures />

    <!-- Social Proof Section -->
    <LandingSocialProof />

    <!-- FAQ Section -->
    <LandingFAQ />

    <!-- CTA Final -->
    <section class="cta-final">
      <div class="cta-final-container">
        <h2 class="cta-final-title">🚀 Rejoignez les beta-testeurs</h2>
        <p class="cta-final-subtitle">
          Gratuit 1 mois • -50% à vie* • Sans engagement
        </p>
        <p class="cta-final-conditions">* Sous conditions de feedback régulier</p>
        <LandingSignupForm :show-full-form="true" />
        <div class="urgency-bar">
          <div class="urgency-progress" :style="{ width: `${(placesRestantes / 100) * 100}%` }"></div>
        </div>
        <p class="urgency-text">{{ placesRestantes }} places restantes sur 100</p>
      </div>
    </section>

    <!-- Beta Conditions Section -->
    <LandingBetaConditions />

    <!-- Footer -->
    <footer class="beta-footer">
      <div class="footer-container">
        <div class="footer-logo">
          <span class="logo-text">STOFLOW</span>
        </div>

        <div class="footer-links">
          <a href="mailto:contact@stoflow.fr" class="footer-link">Contact</a>
        </div>

        <p class="footer-copyright">
          © {{ new Date().getFullYear() }} Stoflow. Tous droits réservés.
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
// SEO Meta tags
useHead({
  title: 'Stoflow Beta - Publiez sur Vinted & eBay en 10 secondes',
  meta: [
    {
      name: 'description',
      content: 'Arrêtez de recopier 10x vos descriptions. Beta gratuite -50% à vie. Publiez automatiquement sur Vinted, eBay, Etsy avec l\'IA.'
    },
    {
      property: 'og:title',
      content: 'Stoflow Beta - Publiez sur Vinted & eBay en 10 secondes'
    },
    {
      property: 'og:description',
      content: 'Arrêtez de recopier 10x vos descriptions. Beta gratuite -50% à vie.'
    },
    {
      property: 'og:type',
      content: 'website'
    },
    {
      name: 'twitter:card',
      content: 'summary_large_image'
    },
    {
      name: 'twitter:title',
      content: 'Stoflow Beta - Publiez sur Vinted & eBay en 10 secondes'
    },
    {
      name: 'twitter:description',
      content: 'Arrêtez de recopier 10x vos descriptions. Beta gratuite -50% à vie.'
    }
  ]
})

// Initialize places counter (cosmetic counter: starts at 88, min 15, max 100)
const PLACES_TOTAL = 100
const PLACES_START = 88
const PLACES_MIN = 15

const placesRestantes = ref(PLACES_START)

onMounted(() => {
  // Initialize places counter from localStorage
  const saved = localStorage.getItem('placesRestantes')
  if (saved) {
    // Clamp between MIN and TOTAL
    placesRestantes.value = Math.max(PLACES_MIN, Math.min(PLACES_TOTAL, parseInt(saved)))
  } else {
    localStorage.setItem('placesRestantes', placesRestantes.value.toString())
  }
})

// Provide to child components
provide('placesRestantes', placesRestantes)
</script>

<style scoped>
.beta-page {
  min-height: 100vh;
  background: white;
}

/* CTA #2 */
.cta-section-2 {
  padding: 4rem 1.5rem;
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
}

.cta-container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.cta-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 2rem;
}

.cta-section-2 .places-counter {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(26, 26, 26, 0.1);
  border: 1px solid rgba(26, 26, 26, 0.2);
  border-radius: 9999px;
  font-size: 0.95rem;
  color: #1a1a1a;
}

.cta-section-2 .counter-icon {
  font-size: 1.2rem;
}

.cta-section-2 .counter-text strong {
  font-weight: 700;
}

/* CTA #2 - Override button colors for visibility on yellow background */
.cta-section-2 :deep(.submit-button) {
  background: #1a1a1a !important;
  color: #facc15 !important;
}

.cta-section-2 :deep(.submit-button:hover:not(:disabled)) {
  background: #2a2a2a !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3) !important;
}

/* CTA Final */
.cta-final {
  padding: 5rem 1.5rem;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
}

.cta-final-container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.cta-final-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 1rem;
  line-height: 1.3;
  padding: 0 1rem;
}

.cta-final-subtitle {
  font-size: 1.25rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.cta-final-conditions {
  font-size: 0.875rem;
  color: #9ca3af;
  font-style: italic;
  margin-bottom: 2rem;
}

.urgency-bar {
  width: 100%;
  height: 12px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.urgency-progress {
  height: 100%;
  background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #22c55e 100%);
  border-radius: 9999px;
  transition: width 0.5s ease;
}

.urgency-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Footer */
.beta-footer {
  padding: 3rem 1.5rem 2rem;
  background: #1a1a1a;
  color: white;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.footer-logo {
  margin-bottom: 1.5rem;
}

.logo-text {
  font-size: 2rem;
  font-weight: 800;
  color: #facc15;
  letter-spacing: 0.05em;
}

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.footer-link {
  color: #d1d5db;
  text-decoration: none;
  font-size: 1rem;
  transition: color 0.3s;
}

.footer-link:hover {
  color: #facc15;
}

.footer-separator {
  color: #6b7280;
}

.footer-copyright {
  color: #6b7280;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .cta-section-2 {
    padding: 3rem 1rem;
  }

  .cta-title {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .cta-section-2 .places-counter {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .cta-final {
    padding: 3rem 1rem;
  }

  .cta-final-title {
    font-size: 1.75rem;
    margin-bottom: 0.75rem;
    line-height: 1.3;
    padding: 0 0.5rem;
  }

  .cta-final-subtitle {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }

  .cta-final-conditions {
    font-size: 0.8125rem;
    margin-bottom: 1.5rem;
  }

  .urgency-bar {
    height: 10px;
    margin-top: 1.5rem;
  }

  .urgency-text {
    font-size: 0.8125rem;
  }

  .beta-footer {
    padding: 2rem 1rem 1.5rem;
  }

  .footer-logo {
    margin-bottom: 1rem;
  }

  .logo-text {
    font-size: 1.5rem;
  }

  .footer-links {
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .footer-link {
    font-size: 0.9375rem;
  }

  .footer-copyright {
    font-size: 0.8125rem;
  }
}
</style>
