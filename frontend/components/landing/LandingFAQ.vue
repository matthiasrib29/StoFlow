<template>
  <section id="faq" class="py-20 lg:py-32 bg-white">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16 animate-on-scroll">
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Questions fréquentes
        </h2>
        <p class="text-xl text-secondary-600">
          Vous avez des questions ? Nous avons les réponses.
        </p>
      </div>

      <div class="space-y-4">
        <div
          v-for="(faq, index) in faqs"
          :key="index"
          class="border-2 border-gray-200 rounded-xl overflow-hidden animate-on-scroll"
        >
          <button
            class="w-full flex items-center justify-between p-6 text-left bg-white hover:bg-gray-50 transition-colors gap-4"
            @click="toggleFaq(index)"
          >
            <div class="flex items-center gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <i :class="['pi', faq.icon, 'text-secondary-700']" />
              </div>
              <h3 class="font-bold text-secondary-900">{{ faq.question }}</h3>
            </div>
            <i
              :class="openFaq === index ? 'pi pi-minus' : 'pi pi-plus'"
              class="text-primary-500 flex-shrink-0"
            />
          </button>
          <div
            v-show="openFaq === index"
            class="px-6 pb-6 pl-20 text-secondary-600"
          >
            {{ faq.answer }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const faqs = [
  {
    icon: 'pi-wallet',
    question: 'Stoflow est-il vraiment gratuit ?',
    answer: 'Oui ! Notre plan gratuit vous permet de gérer jusqu\'à 10 produits sur une marketplace sans aucun frais. C\'est parfait pour découvrir la plateforme. Pour plus de fonctionnalités, nos plans payants commencent à 19€/mois.'
  },
  {
    icon: 'pi-link',
    question: 'Comment fonctionne la connexion aux marketplaces ?',
    answer: 'Nous utilisons une extension navigateur sécurisée pour Vinted (qui n\'a pas d\'API publique) et des connexions OAuth officielles pour eBay et Etsy. Vos identifiants ne transitent jamais par nos serveurs.'
  },
  {
    icon: 'pi-shield',
    question: 'Mes données sont-elles sécurisées ?',
    answer: 'Absolument. Nous utilisons un chiffrement de niveau bancaire (AES-256) pour toutes vos données. Nos serveurs sont hébergés en Europe et nous sommes 100% conformes RGPD.'
  },
  {
    icon: 'pi-times-circle',
    question: 'Puis-je annuler à tout moment ?',
    answer: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis votre espace client. Pas de période d\'engagement, pas de frais cachés. Vous gardez l\'accès jusqu\'à la fin de votre période payée.'
  },
  {
    icon: 'pi-sparkles',
    question: 'La génération IA est-elle incluse ?',
    answer: 'La génération de descriptions par IA est incluse dans les plans Pro (100 générations/mois) et Business (illimité). Le plan gratuit n\'inclut pas cette fonctionnalité.'
  },
  {
    icon: 'pi-clock',
    question: 'Combien de temps pour configurer Stoflow ?',
    answer: 'Moins de 5 minutes ! Créez votre compte, installez l\'extension navigateur, connectez vos marketplaces et vous êtes prêt. L\'import de vos produits existants est automatique.'
  },
  {
    icon: 'pi-desktop',
    question: 'L\'extension fonctionne-t-elle sur tous les navigateurs ?',
    answer: 'Notre extension est disponible sur Chrome et Firefox (les deux navigateurs les plus utilisés). Une version Edge est en cours de développement.'
  },
  {
    icon: 'pi-shopping-cart',
    question: 'Que se passe-t-il si un produit est vendu ?',
    answer: 'Lorsqu\'un produit est vendu sur une plateforme, Stoflow met automatiquement à jour le stock sur toutes vos autres marketplaces. Fini les surventes et les annulations !'
  }
]

const openFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  openFaq.value = openFaq.value === index ? null : index
}
</script>
