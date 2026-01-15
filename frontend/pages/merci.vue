<template>
  <div class="merci-page">
    <div class="merci-container">
      <div class="success-icon">✅</div>

      <h1 class="merci-title">Vous êtes inscrit à la beta !</h1>

      <div class="merci-content">
        <div class="info-box">
          <div class="info-item">
            <span class="info-icon">📧</span>
            <p>Vérifiez votre email (spam si besoin)</p>
          </div>
          <div class="info-item">
            <span class="info-icon">⏰</span>
            <p>On vous contacte dans 48h avec vos accès</p>
          </div>
        </div>

        <div class="social-section">
          <h2 class="social-title">En attendant :</h2>

          <div class="social-links">
            <a href="#" class="social-link discord" @click.prevent>
              <span class="social-icon">💬</span>
              <span>Rejoignez notre Discord</span>
            </a>
            <a href="#" class="social-link twitter" @click.prevent>
              <span class="social-icon">🐦</span>
              <span>Suivez-nous sur Twitter</span>
            </a>
          </div>
        </div>

        <div class="bonus-section">
          <div class="bonus-box">
            <div class="bonus-icon">🎁</div>
            <h3 class="bonus-title">BONUS : Partagez avec 3 amis</h3>
            <p class="bonus-description">Gagnez 1 mois gratuit supplémentaire</p>

            <div class="share-buttons">
              <button class="share-button whatsapp" @click="shareWhatsApp">
                <span>WhatsApp</span>
              </button>
              <button class="share-button twitter" @click="shareTwitter">
                <span>Twitter</span>
              </button>
              <button class="share-button email" @click="shareEmail">
                <span>Email</span>
              </button>
            </div>
          </div>
        </div>

        <NuxtLink to="/beta" class="back-button">
          ← Retour à l'accueil
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// SEO Meta tags
useHead({
  title: 'Merci pour votre inscription - Stoflow Beta',
  meta: [
    {
      name: 'description',
      content: 'Inscription confirmée ! Vérifiez votre email pour recevoir vos accès beta.'
    },
    {
      name: 'robots',
      content: 'noindex'
    }
  ]
})

const shareUrl = 'https://stoflow.fr/beta'
const shareText = 'Stoflow : publiez sur Vinted & eBay en 10 secondes avec l\'IA. Beta gratuite -50% à vie !'

const shareWhatsApp = () => {
  const url = `https://wa.me/?text=${encodeURIComponent(shareText + ' ' + shareUrl)}`
  window.open(url, '_blank')
}

const shareTwitter = () => {
  const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`
  window.open(url, '_blank')
}

const shareEmail = () => {
  const subject = encodeURIComponent('Découvre Stoflow - Publication automatique sur Vinted & eBay')
  const body = encodeURIComponent(`${shareText}\n\n${shareUrl}`)
  window.location.href = `mailto:?subject=${subject}&body=${body}`
}
</script>

<style scoped>
.merci-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
}

.merci-container {
  max-width: 700px;
  width: 100%;
  background: white;
  border-radius: 2rem;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.success-icon {
  font-size: 5rem;
  margin-bottom: 1.5rem;
  animation: bounce 1s ease-in-out;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.merci-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 2rem;
}

.merci-content {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.info-box {
  background: #f9fafb;
  border-radius: 1rem;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
}

.info-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.info-item p {
  font-size: 1.1rem;
  color: #1a1a1a;
  margin: 0;
}

.social-section {
  margin: 1rem 0;
}

.social-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #1a1a1a;
}

.social-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 2rem;
  border-radius: 0.75rem;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.3s;
}

.social-link.discord {
  background: #5865F2;
  color: white;
}

.social-link.discord:hover {
  background: #4752C4;
  transform: translateY(-2px);
}

.social-link.twitter {
  background: #1DA1F2;
  color: white;
}

.social-link.twitter:hover {
  background: #1A91DA;
  transform: translateY(-2px);
}

.social-icon {
  font-size: 1.5rem;
}

.bonus-section {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  border-radius: 1rem;
  padding: 2rem;
}

.bonus-box {
  color: #1a1a1a;
}

.bonus-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.bonus-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.bonus-description {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  opacity: 0.9;
}

.share-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.share-button {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
}

.share-button.whatsapp {
  background: #25D366;
}

.share-button.whatsapp:hover {
  background: #1DA851;
  transform: translateY(-2px);
}

.share-button.twitter {
  background: #1DA1F2;
}

.share-button.twitter:hover {
  background: #1A91DA;
  transform: translateY(-2px);
}

.share-button.email {
  background: #6b7280;
}

.share-button.email:hover {
  background: #4b5563;
  transform: translateY(-2px);
}

.back-button {
  display: inline-block;
  padding: 1rem 2rem;
  background: #1a1a1a;
  color: white;
  text-decoration: none;
  border-radius: 0.75rem;
  font-weight: 600;
  transition: all 0.3s;
}

.back-button:hover {
  background: #2a2a2a;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .merci-container {
    padding: 2rem 1.5rem;
  }

  .social-links {
    gap: 0.75rem;
  }

  .social-link {
    font-size: 1rem;
    padding: 0.875rem 1.5rem;
  }

  .share-buttons {
    flex-direction: column;
  }

  .share-button {
    width: 100%;
  }
}
</style>
