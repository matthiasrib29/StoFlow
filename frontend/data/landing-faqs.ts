export interface LandingFaq {
  icon: string
  question: string
  answer: string
}

export const landingFaqs: LandingFaq[] = [
  {
    icon: 'pi-wallet',
    question: 'Stoflow est-il vraiment gratuit ?',
    answer: 'Oui ! Notre plan gratuit vous permet de gérer jusqu\'à 10 produits sur une marketplace sans aucun frais. C\'est parfait pour découvrir la plateforme. Pour plus de fonctionnalités, nos plans payants commencent à 19€/mois.'
  },
  {
    icon: 'pi-link',
    question: 'Comment fonctionne la connexion aux marketplaces ?',
    // PMV2: Etsy removed from answer
    answer: 'Nous utilisons une extension navigateur sécurisée pour Vinted (qui n\'a pas d\'API publique) et des connexions OAuth officielles pour eBay. Vos identifiants ne transitent jamais par nos serveurs.'
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
