<template>
  <section class="pricing-section">
    <div class="section-container">
      <h2 class="section-title">💰 Offre Beta Exclusive</h2>

      <div class="pricing-cards">
        <div class="pricing-card regular">
          <div class="card-header">
            <h3>Après Beta</h3>
          </div>
          <div class="card-price">
            <span class="price-amount">29€</span>
            <span class="price-period">/mois</span>
          </div>
          <ul class="card-features">
            <li>✅ Publications illimitées</li>
            <li>✅ IA descriptions</li>
            <li>✅ Vinted + eBay</li>
            <li>✅ Support email</li>
          </ul>
        </div>

        <div class="pricing-card beta">
          <div class="card-badge">🔥 OFFRE LIMITÉE</div>
          <div class="card-header">
            <h3>Beta (100 premiers)</h3>
          </div>
          <div class="card-price">
            <span class="price-old">29€</span>
            <span class="price-amount">14,50€</span>
            <span class="price-period">/mois</span>
          </div>
          <div class="card-discount">-50% À VIE 🎉</div>
          <ul class="card-features">
            <li>✅ <strong>Tout inclus</strong></li>
            <li>✅ <strong>1 mois gratuit</strong></li>
            <li>✅ <strong>Sans engagement</strong></li>
            <li>✅ <strong>Support prioritaire</strong></li>
          </ul>
          <div class="card-cta">
            <p class="cta-text">⏰ Plus que <strong>{{ placesRestantes }}/100</strong> places</p>
          </div>
        </div>
      </div>

      <p class="pricing-note">
        💡 <strong>1 mois gratuit offert</strong> pour tester. Annulez à tout moment sans frais.
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
const placesRestantes = inject<Ref<number>>('placesRestantes')!
</script>

<style scoped>
.pricing-section {
  padding: 5rem 1.5rem;
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
  color: white;
}

.section-container {
  max-width: 1000px;
  margin: 0 auto;
}

.section-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 700;
  text-align: center;
  margin-bottom: 4rem;
}

.pricing-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.pricing-card {
  background: white;
  color: #1a1a1a;
  padding: 2.5rem;
  border-radius: 1.5rem;
  position: relative;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.pricing-card:hover {
  transform: translateY(-8px);
}

.pricing-card.beta {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  transform: scale(1.05);
  box-shadow: 0 16px 32px rgba(250, 204, 21, 0.3);
}

.pricing-card.beta:hover {
  transform: scale(1.08) translateY(-8px);
}

.card-badge {
  position: absolute;
  top: -1rem;
  left: 50%;
  transform: translateX(-50%);
  background: #ef4444;
  color: white;
  padding: 0.5rem 1.5rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.card-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  text-align: center;
}

.card-price {
  text-align: center;
  margin-bottom: 1rem;
}

.price-old {
  font-size: 1.5rem;
  text-decoration: line-through;
  color: #6b7280;
  margin-right: 0.5rem;
}

.price-amount {
  font-size: 3rem;
  font-weight: 700;
  color: #1a1a1a;
}

.price-period {
  font-size: 1.25rem;
  color: #6b7280;
}

.card-discount {
  text-align: center;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 2rem;
}

.card-features {
  list-style: none;
  padding: 0;
  margin: 2rem 0;
}

.card-features li {
  padding: 0.75rem 0;
  font-size: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.card-features li:last-child {
  border-bottom: none;
}

.card-cta {
  margin-top: 2rem;
  text-align: center;
}

.cta-text {
  font-size: 1rem;
  padding: 1rem;
  background: rgba(26, 26, 26, 0.1);
  border-radius: 0.5rem;
}

.cta-text strong {
  color: #1a1a1a;
  font-weight: 700;
}

.pricing-note {
  text-align: center;
  color: #d1d5db;
  font-size: 1.1rem;
  margin-top: 2rem;
}

@media (max-width: 768px) {
  .pricing-section {
    padding: 3rem 1rem;
  }

  .pricing-cards {
    grid-template-columns: 1fr;
  }

  .pricing-card.beta {
    transform: scale(1);
  }

  .pricing-card.beta:hover {
    transform: translateY(-8px);
  }
}
</style>
