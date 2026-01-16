<template>
  <section class="conditions-section">
    <div class="conditions-container">
      <p class="conditions-text">
        <strong>Conditions du tarif -50% à vie :</strong> Feedback régulier • Utilisation active de la plateforme • Participation à l'amélioration de Stoflow
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
// Beta conditions component
</script>

<style scoped>
.conditions-section {
  padding: 2rem 1.5rem;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.conditions-container {
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
}

.conditions-text {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

.conditions-text strong {
  color: #1a1a1a;
  font-weight: 600;
}

@media (max-width: 768px) {
  .conditions-section {
    padding: 1.5rem 1rem;
  }

  .conditions-text {
    font-size: 0.8125rem;
  }
}
</style>
