<template>
  <section class="social-proof-section">
    <div class="section-container">
      <h2 class="section-title">👋 Qui est derrière Stoflow ?</h2>

      <div class="founder-story">
        <div class="founder-card">
          <div class="founder-header">
            <div class="founder-image-wrapper">
              <img
                src="/images/matthias-shop-ton-outfit.jpg"
                alt="Matthias devant Shop Ton Outfit"
                class="founder-image"
              />
            </div>
            <div class="founder-text">
              <h3 class="founder-name">Je m'appelle Matthias</h3>
              <p class="founder-subtitle">Fondateur de Stoflow & Shop Ton Outfit</p>
            </div>
          </div>

          <div class="founder-story-text">
            <p>Je gère <strong>Shop Ton Outfit</strong>, ma boutique de seconde-main depuis 3 ans. Ingénieur de formation, vendeur actif sur Vinted, eBay et Etsy au quotidien.</p>

            <p>J'en avais MARRE de recopier 10x les mêmes descriptions, de perdre 2h pour publier 10 produits, de faire des erreurs entre les plateformes...</p>

            <p><strong>Alors j'ai développé Stoflow. D'abord pour moi.</strong></p>

            <p>Aujourd'hui je gagne <strong>90% de temps</strong> sur mes publications.</p>

            <p>Si ça peut vous aider aussi, je partage l'outil 🙏</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
// Founder story replaces fake testimonials for authenticity
</script>

<style scoped>
.social-proof-section {
  padding: 5rem 1.5rem;
  background: white;
}

.section-container {
  max-width: 900px;
  margin: 0 auto;
}

.section-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 700;
  text-align: center;
  margin-bottom: 3rem;
  color: #1a1a1a;
}

.founder-story {
  display: flex;
  justify-content: center;
}

.founder-card {
  background: #f9fafb;
  padding: 3rem;
  border-radius: 1rem;
  border: 2px solid #facc15;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  max-width: 700px;
  width: 100%;
}

.founder-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.founder-image-wrapper {
  flex-shrink: 0;
}

.founder-image {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  object-fit: cover;
  object-position: center 20%;
  border: 4px solid #facc15;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.founder-text {
  flex: 1;
}

.founder-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.founder-subtitle {
  font-size: 1rem;
  color: #6b7280;
  font-weight: 500;
}

.founder-story-text {
  margin-bottom: 2rem;
  font-size: 1.05rem;
  line-height: 1.8;
  color: #1a1a1a;
}

.founder-story-text p {
  margin-bottom: 1rem;
}

.founder-story-text p:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .social-proof-section {
    padding: 3rem 1rem;
  }

  .section-title {
    margin-bottom: 2rem;
  }

  .founder-card {
    padding: 2rem;
  }

  .founder-header {
    flex-direction: column;
    text-align: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
  }

  .founder-image {
    width: 130px;
    height: 130px;
  }

  .founder-name {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
  }

  .founder-subtitle {
    font-size: 0.9375rem;
  }

  .founder-story-text {
    font-size: 1rem;
    margin-bottom: 1.5rem;
  }
}
</style>
