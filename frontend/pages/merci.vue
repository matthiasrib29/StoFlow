<template>
  <div class="merci-page">
    <div class="merci-container">
      <div class="success-icon">
        <i class="pi pi-check-circle"></i>
      </div>

      <h1 class="merci-title">Vous êtes inscrit à la beta !</h1>

      <div class="merci-content">
        <div class="info-box">
          <div class="info-item">
            <i class="pi pi-envelope info-icon-svg"></i>
            <p>Vérifiez votre email (spam si besoin)</p>
          </div>
        </div>

        <div class="social-section">
          <h2 class="social-title">En attendant :</h2>

          <div class="social-links">
            <a href="https://discord.gg/NZh8FYgjuk" target="_blank" class="social-link discord">
              <i class="pi pi-discord"></i>
              <span>Rejoindre le Discord</span>
            </a>
          </div>
        </div>

        <div class="share-section">
          <h2 class="share-title">Envie d'en parler ?</h2>
          <p class="share-description">Partagez avec vos amis vendeurs</p>

          <div class="share-buttons">
            <button class="share-button whatsapp" @click="shareWhatsApp">
              <i class="pi pi-whatsapp"></i>
              <span>WhatsApp</span>
            </button>
            <button class="share-button instagram" @click="shareInstagram">
              <i class="pi pi-instagram"></i>
              <span>Instagram</span>
            </button>
            <button class="share-button tiktok" @click="shareTikTok">
              <svg class="tiktok-icon" viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
              </svg>
              <span>TikTok</span>
            </button>
            <button class="share-button email" @click="shareEmail">
              <i class="pi pi-envelope"></i>
              <span>Email</span>
            </button>
          </div>
        </div>

        <NuxtLink to="/beta" class="back-link">
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

const shareInstagram = async () => {
  // Use native Web Share API on mobile, fallback to copy link
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Stoflow Beta',
        text: shareText,
        url: shareUrl
      })
    } catch (err) {
      console.log('Share cancelled')
    }
  } else {
    // Fallback: copy link to clipboard
    await navigator.clipboard.writeText(shareUrl)
    alert('Lien copié ! Collez-le dans votre story Instagram')
  }
}

const shareTikTok = async () => {
  // Use native Web Share API on mobile, fallback to copy link
  if (navigator.share) {
    try {
      await navigator.share({
        title: 'Stoflow Beta',
        text: shareText,
        url: shareUrl
      })
    } catch (err) {
      console.log('Share cancelled')
    }
  } else {
    // Fallback: copy link to clipboard
    await navigator.clipboard.writeText(shareUrl)
    alert('Lien copié ! Collez-le dans votre vidéo TikTok')
  }
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
  background: #f9fafb;
}

.merci-container {
  max-width: 700px;
  width: 100%;
  background: white;
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  text-align: center;
}

.success-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  color: #facc15;
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
  background: #fffef5;
  border-radius: 1rem;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  border: 2px solid #facc15;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
}

.info-icon-svg {
  font-size: 1.5rem;
  flex-shrink: 0;
  color: #facc15;
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
  gap: 0.75rem;
  padding: 0.875rem 1.75rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s;
  border: 2px solid #5865F2;
  background: #5865F2;
  color: white;
}

.social-link.discord i {
  color: white;
}

.social-link.discord:hover {
  background: #4752C4;
  border-color: #4752C4;
  transform: translateY(-2px);
}

.social-link.twitter:hover {
  border-color: #1DA1F2;
  background: #e8f5ff;
}

.social-link i {
  font-size: 1.25rem;
  color: #6b7280;
}

.share-section {
  background: #fafafa;
  border: 1.5px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 2rem;
}

.share-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #1a1a1a;
}

.share-title::before {
  content: "✨ ";
}

.share-description {
  font-size: 1rem;
  margin-bottom: 1.5rem;
  color: #6b7280;
}

.share-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.share-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: 1.5px solid #e5e7eb;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  color: #1a1a1a;
}

.share-button i,
.share-button .tiktok-icon {
  font-size: 1.1rem;
}

.share-button.whatsapp:hover {
  border-color: #25D366;
  background: #e8f8f0;
}

.share-button.instagram:hover {
  border-color: #E1306C;
  background: #ffe8f0;
}

.share-button.tiktok:hover {
  border-color: #000000;
  background: #f3f4f6;
}

.share-button.email:hover {
  border-color: #6b7280;
  background: #f3f4f6;
}

.back-link {
  color: #6b7280;
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.2s;
}

.back-link:hover {
  color: #1a1a1a;
}

@media (max-width: 768px) {
  .merci-page {
    padding: 1rem;
  }

  .merci-container {
    padding: 2rem 1.25rem;
  }

  .success-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .merci-title {
    font-size: 1.75rem;
    margin-bottom: 1.5rem;
  }

  .merci-content {
    gap: 2rem;
  }

  .info-box {
    padding: 1.5rem;
  }

  .info-item p {
    font-size: 1rem;
  }

  .social-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  .social-links {
    gap: 0.75rem;
  }

  .social-link {
    font-size: 0.9375rem;
    padding: 0.875rem 1.25rem;
    min-height: 48px;
  }

  .share-section {
    padding: 1.5rem;
  }

  .share-title {
    font-size: 1.25rem;
  }

  .share-description {
    font-size: 0.9375rem;
    margin-bottom: 1.25rem;
  }

  .share-buttons {
    flex-direction: column;
    gap: 0.75rem;
  }

  .share-button {
    width: 100%;
    padding: 0.875rem 1.25rem;
    font-size: 0.9375rem;
    min-height: 48px;
  }

  .back-link {
    font-size: 0.8125rem;
  }
}
</style>
