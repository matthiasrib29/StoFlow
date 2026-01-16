<template>
  <section class="problem-section">
    <div class="section-container">
      <h2 class="section-title">😤 Vous en avez marre de...</h2>

      <div class="problems-grid">
        <div v-for="problem in problems" :key="problem.title" class="problem-card">
          <div class="problem-icon">❌</div>
          <h3 class="problem-title">{{ problem.title }}</h3>
          <p class="problem-description">{{ problem.description }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const problems = [
  {
    title: 'Recopier les mêmes descriptions 10 fois',
    description: 'Chaque marketplace a son format. Vous perdez 15 minutes par produit.'
  },
  {
    title: 'Passer 2h à publier 10 produits',
    description: 'Upload photo, remplir les champs, vérifier... et recommencer sur eBay, Vinted, Etsy...'
  },
  {
    title: 'Jongler entre 5 onglets',
    description: 'Vinted, eBay, Etsy, Excel, Photos... Votre navigateur devient ingérable.'
  }
]
</script>

<style scoped>
.problem-section {
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
  margin-bottom: 3rem;
  color: #1a1a1a;
}

.problems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.problem-card {
  background: white;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.problem-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
}

.problem-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.problem-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1a1a1a;
}

.problem-description {
  color: #6b7280;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .problem-section {
    padding: 3rem 1rem;
  }

  .problems-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}
</style>
