<template>
  <div>
    <!-- Hero Section -->
    <LandingHero @show-demo="handleShowDemo" />

    <!-- Stats Counter Section -->
    <LandingStatsCounter />

    <!-- Trust Badges Section -->
    <LandingTrustBadges />

    <!-- Platforms Section -->
    <LandingPlatforms />

    <!-- Features Section -->
    <LandingFeatures />

    <!-- Why Stoflow Section -->
    <LandingWhyStoflow />

    <!-- How It Works Section -->
    <LandingHowItWorks />

    <!-- Pricing Section -->
    <LandingPricing
      :plans="plans"
      :loading="pricingLoading"
      :get-annual-price="getAnnualPrice"
      :get-annual-savings="getAnnualSavings"
      @plan-click="handlePlanClick"
    />

    <!-- Testimonials Section -->
    <LandingTestimonials />

    <!-- FAQ Section -->
    <LandingFAQ />

    <!-- CTA Section -->
    <LandingCTASection @show-demo="handleShowDemo" />

    <!-- Sticky CTA Mobile -->
    <LandingStickyCTA />

    <!-- Exit Intent Popup -->
    <LandingExitIntentPopup />
  </div>
</template>

<script setup lang="ts">
import type { PricingPlan } from '~/composables/usePricing'

definePageMeta({
  layout: 'landing'
})

// SEO Meta Tags
useSeoHead({
  title: 'Gérez Vinted, eBay & Etsy',
  description: 'Centralisez vos ventes sur Vinted, eBay, Etsy. Synchronisation automatique, publication en un clic, gestion des stocks simplifiée. Essai gratuit 14 jours.',
  ogImage: '/images/og-stoflow.jpg'
})

// Structured Data (Schema.org JSON-LD)
useOrganizationSchema()
useSoftwareApplicationSchema()

// Pricing - Dynamic from API
const { plans, loading: pricingLoading, fetchPricingPlans, getAnnualPrice, getAnnualSavings } = usePricing()

// Fetch pricing plans and setup scroll animations on mount
onMounted(async () => {
  await fetchPricingPlans()
  setupScrollAnimations()
})

// Setup scroll animation observer
const setupScrollAnimations = () => {
  setTimeout(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.1, rootMargin: '50px' }
    )

    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
      observer.observe(el)
    })
  }, 100)
}

// Handle plan CTA click
const handlePlanClick = (plan: PricingPlan) => {
  if (plan.tier === 'enterprise') {
    window.location.href = 'mailto:contact@stoflow.io?subject=Enterprise Plan'
  } else {
    navigateTo('/register')
  }
}

// Handle demo button click
const handleShowDemo = () => {
  // TODO: Implement demo modal or redirect
}
</script>

<style>
/* Scroll-triggered animations - global for child components */
.animate-on-scroll {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

.animate-on-scroll:not(.animate-visible) {
  opacity: 0;
  transform: translateY(30px);
}

@media (prefers-reduced-motion: reduce) {
  .animate-on-scroll {
    opacity: 1 !important;
    transform: none !important;
  }
}

.animate-on-scroll.animation-delay-200 {
  transition-delay: 0.2s;
}

.animate-on-scroll.animation-delay-400 {
  transition-delay: 0.4s;
}
</style>
