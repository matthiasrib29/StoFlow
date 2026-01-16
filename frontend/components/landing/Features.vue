<template>
  <section class="features-section">
    <div class="section-container">
      <h2 class="section-title">✨ Tout ce dont vous avez besoin</h2>

      <div class="features-grid">
        <div v-for="feature in features" :key="feature.title" class="feature-card">
          <div class="feature-icon">{{ feature.icon }}</div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const features = [
  {
    icon: '✅',
    title: 'Descriptions IA optimisées',
    description: 'Descriptions SEO parfaites générées en 2 secondes par notre IA'
  },
  {
    icon: '✅',
    title: 'Publication Vinted + eBay simultanée',
    description: 'Un clic et votre produit est publié sur toutes les marketplaces'
  },
  {
    icon: '✅',
    title: 'Gestion multi-produits en masse',
    description: 'Importez 100 produits d\'un coup, on s\'occupe de tout'
  }
]
</script>

<style scoped>
.features-section {
  padding: 5rem 1.5rem;
  background: #f9fafb;
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

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  padding: 2.5rem;
  border-radius: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1a1a1a;
}

.feature-description {
  color: #6b7280;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .features-section {
    padding: 3rem 1rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}
</style>
