<template>
  <div class="beta-page">
    <!-- Hero Section -->
    <LandingHero />

    <!-- Problem Section -->
    <LandingProblem />

    <!-- How It Works Section -->
    <LandingHowItWorks />

    <!-- Features Section -->
    <LandingFeatures />

    <!-- Pricing Section -->
    <LandingPricing />

    <!-- FAQ Section -->
    <LandingFAQ />

    <!-- Final CTA Section -->
    <section class="final-cta-section">
      <div class="cta-container">
        <h2 class="cta-title">Prêt à gagner 90% de temps ?</h2>
        <p class="cta-subtitle">Rejoignez les {{ 50 - placesRestantes }} vendeurs déjà inscrits</p>

        <LandingSignupForm />

        <p class="cta-note">
          ✅ Gratuit pendant 1 mois | ✅ -50% à vie | ✅ Sans engagement
        </p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="beta-footer">
      <div class="footer-container">
        <div class="footer-logo">
          <span class="logo-text">STOFLOW</span>
        </div>

        <div class="footer-links">
          <NuxtLink to="/login" class="footer-link">Connexion</NuxtLink>
          <span class="footer-separator">•</span>
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

// Initialize places counter (fake localStorage-based counter)
const placesRestantes = ref(38)

onMounted(() => {
  const saved = localStorage.getItem('placesRestantes')
  if (saved) {
    placesRestantes.value = Math.max(0, Math.min(50, parseInt(saved)))
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

/* Final CTA Section */
.final-cta-section {
  padding: 5rem 1.5rem;
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
}

.cta-container {
  max-width: 700px;
  margin: 0 auto;
  text-align: center;
}

.cta-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 1rem;
}

.cta-subtitle {
  font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  color: #1a1a1a;
  margin-bottom: 3rem;
  opacity: 0.9;
}

.cta-note {
  margin-top: 2rem;
  font-size: 1.1rem;
  color: #1a1a1a;
  font-weight: 600;
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
  .final-cta-section {
    padding: 3rem 1rem;
  }

  .footer-links {
    flex-wrap: wrap;
  }
}
</style>
