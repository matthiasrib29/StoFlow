<template>
  <section class="faq-section">
    <div class="section-container">
      <h2 class="section-title">❓ Questions Fréquentes</h2>

      <div class="faq-list">
        <div
          v-for="(item, index) in faqItems"
          :key="index"
          class="faq-item"
          :class="{ open: openIndex === index }"
        >
          <button class="faq-question-btn" @click="toggleItem(index)">
            <span class="faq-question">{{ item.question }}</span>
            <span class="faq-icon">{{ openIndex === index ? '−' : '+' }}</span>
          </button>
          <div v-if="openIndex === index" class="faq-answer">
            {{ item.answer }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const openIndex = ref<number | null>(null)

const faqItems = [
  {
    question: 'Dois-je payer pour la beta ?',
    answer: 'Non ! La beta est gratuite pendant 1 mois complet. Après, vous bénéficiez de -50% à vie (9.99€/mois au lieu de 19.99€ pour le plan Pro) tant que vous donnez du feedback régulier et participez à l\'amélioration de Stoflow.'
  },
  {
    question: 'Quelles marketplaces sont supportées ?',
    answer: 'Au lancement de la beta, Vinted et eBay sont disponibles. Etsy arrive dans les semaines suivantes.'
  },
  {
    question: 'Mes données sont-elles sécurisées ?',
    answer: 'Oui à 100%. Stoflow est RGPD compliant. Vos données sont chiffrées et jamais partagées. Vous pouvez supprimer votre compte à tout moment.'
  },
  {
    question: 'Puis-je annuler à tout moment ?',
    answer: 'Absolument ! Aucun engagement. Annulez en 1 clic depuis votre tableau de bord, sans justification.'
  },
  {
    question: 'L\'IA fait-elle des erreurs ?',
    answer: 'Notre IA a un taux de précision de 95%+. Vous pouvez toujours vérifier et modifier les descriptions avant publication.'
  }
]

const toggleItem = (index: number) => {
  openIndex.value = openIndex.value === index ? null : index
}
</script>

<style scoped>
.faq-section {
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

.faq-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.faq-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
  transition: all 0.3s;
}

.faq-item.open {
  border-color: #facc15;
  box-shadow: 0 4px 12px rgba(250, 204, 21, 0.15);
}

.faq-question-btn {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: white;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.3s;
}

.faq-question-btn:hover {
  background: #f9fafb;
}

.faq-question {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1a1a1a;
}

.faq-icon {
  font-size: 1.5rem;
  font-weight: 700;
  color: #facc15;
  flex-shrink: 0;
  margin-left: 1rem;
}

.faq-answer {
  padding: 1.5rem;
  background: #f9fafb;
  color: #6b7280;
  line-height: 1.7;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .faq-section {
    padding: 3rem 1rem;
  }

  .faq-question-btn {
    padding: 1rem;
  }

  .faq-question {
    font-size: 1rem;
  }

  .faq-answer {
    padding: 1rem;
  }
}
</style>
