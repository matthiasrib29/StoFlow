<template>
  <div>
    <LayoutHeaderPublic />

    <main class="min-h-screen bg-gray-50 pt-24 pb-16">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Breadcrumb -->
        <nav class="mb-8">
          <NuxtLink to="/legal" class="text-primary-600 hover:underline flex items-center gap-2">
            <i class="pi pi-arrow-left" />
            Retour aux informations légales
          </NuxtLink>
        </nav>

        <!-- Header -->
        <div class="mb-10">
          <h1 class="text-4xl font-bold text-secondary-900 mb-4">
            Politique de Confidentialité
          </h1>
          <p class="text-gray-500">
            Dernière mise à jour : {{ lastUpdate }}
          </p>
        </div>

        <!-- RGPD Banner -->
        <div class="bg-purple-50 border border-purple-200 rounded-xl p-6 mb-8">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <i class="pi pi-shield text-purple-600 text-xl" />
            </div>
            <div>
              <h2 class="font-bold text-purple-900 mb-2">Conformité RGPD</h2>
              <p class="text-purple-700 text-sm">
                Cette politique de confidentialité est conforme au Règlement Général sur la Protection des Données
                (RGPD - Règlement UE 2016/679) et à la loi Informatique et Libertés du 6 janvier 1978 modifiée.
              </p>
            </div>
          </div>
        </div>

        <!-- Table of contents -->
        <div class="bg-purple-50 rounded-xl p-6 mb-8">
          <h2 class="font-bold text-secondary-900 mb-3">Sommaire</h2>
          <ol class="list-decimal list-inside space-y-1 text-gray-700">
            <li><a href="#responsable" class="hover:text-primary-600">Responsable du traitement</a></li>
            <li><a href="#donnees" class="hover:text-primary-600">Données collectées</a></li>
            <li><a href="#finalites" class="hover:text-primary-600">Finalités du traitement</a></li>
            <li><a href="#base" class="hover:text-primary-600">Base légale</a></li>
            <li><a href="#destinataires" class="hover:text-primary-600">Destinataires des données</a></li>
            <li><a href="#conservation" class="hover:text-primary-600">Durée de conservation</a></li>
            <li><a href="#droits" class="hover:text-primary-600">Vos droits</a></li>
            <li><a href="#cookies" class="hover:text-primary-600">Cookies</a></li>
            <li><a href="#securite" class="hover:text-primary-600">Sécurité</a></li>
            <li><a href="#transferts" class="hover:text-primary-600">Transferts de données</a></li>
            <li><a href="#modifications" class="hover:text-primary-600">Modifications</a></li>
            <li><a href="#contact" class="hover:text-primary-600">Contact</a></li>
          </ol>
        </div>

        <!-- Content -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">
          <!-- Article 1 -->
          <section id="responsable">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 1 - Responsable du traitement
            </h2>
            <div class="bg-gray-50 rounded-lg p-6">
              <p><strong>Raison sociale :</strong> Stokode SARL</p>
              <p><strong>Adresse :</strong> 5 rue Emile Zola, 77340 Pontault-Combault, France</p>
              <p><strong>SIRET :</strong> 992 682 393 00010</p>
              <p><strong>Email DPO :</strong> <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a></p>
              <p><strong>Représentant légal :</strong> Matthias Ribeiro, Gérant</p>
            </div>
          </section>

          <!-- Article 2 -->
          <section id="donnees">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 2 - Données collectées
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Dans le cadre de l'utilisation du service StoFlow, nous collectons les catégories de données
                personnelles suivantes :
              </p>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">2.1 Données d'identification</h3>
              <ul>
                <li>Nom et prénom</li>
                <li>Adresse email</li>
                <li>Mot de passe (stocké de manière chiffrée)</li>
              </ul>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">2.2 Données de facturation</h3>
              <ul>
                <li>Adresse de facturation</li>
                <li>Pays</li>
                <li>Historique des transactions</li>
              </ul>
              <p class="text-sm text-gray-500 mt-2">
                Note : Les données de carte bancaire sont traitées directement par Stripe et ne sont jamais
                stockées sur nos serveurs.
              </p>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">2.3 Données techniques</h3>
              <ul>
                <li>Adresse IP</li>
                <li>Type de navigateur</li>
                <li>Données de connexion (date, heure)</li>
              </ul>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">2.4 Données d'utilisation</h3>
              <ul>
                <li>Actions effectuées sur la plateforme</li>
                <li>Produits créés et publiés</li>
                <li>Statistiques d'utilisation des fonctionnalités</li>
              </ul>
            </div>
          </section>

          <!-- Article 3 -->
          <section id="finalites">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 3 - Finalités du traitement
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Vos données personnelles sont collectées et traitées pour les finalités suivantes :
              </p>
              <table class="w-full mt-4">
                <thead>
                  <tr class="bg-gray-100">
                    <th class="text-left p-3 font-semibold">Finalité</th>
                    <th class="text-left p-3 font-semibold">Données concernées</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b">
                    <td class="p-3">Création et gestion de votre compte</td>
                    <td class="p-3">Identité, email, mot de passe</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Fourniture du service StoFlow</td>
                    <td class="p-3">Toutes les données</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Facturation et paiement</td>
                    <td class="p-3">Identité, adresse de facturation</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Communication (support, notifications)</td>
                    <td class="p-3">Email</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Amélioration du service</td>
                    <td class="p-3">Données d'utilisation</td>
                  </tr>
                  <tr>
                    <td class="p-3">Obligations légales</td>
                    <td class="p-3">Toutes les données requises</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <!-- Article 4 -->
          <section id="base">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 4 - Base légale du traitement
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Conformément au RGPD, chaque traitement de données repose sur une base légale :
              </p>
              <ul>
                <li>
                  <strong>Exécution du contrat (Article 6.1.b)</strong> : Le traitement est nécessaire à
                  l'exécution du contrat d'abonnement (création de compte, fourniture du service, facturation).
                </li>
                <li>
                  <strong>Intérêt légitime (Article 6.1.f)</strong> : Le traitement est nécessaire aux fins
                  des intérêts légitimes poursuivis par Stokode SARL (amélioration du service, sécurité).
                </li>
                <li>
                  <strong>Obligation légale (Article 6.1.c)</strong> : Le traitement est nécessaire au respect
                  d'obligations légales (conservation des données de facturation).
                </li>
                <li>
                  <strong>Consentement (Article 6.1.a)</strong> : Pour les traitements optionnels (newsletter,
                  communications marketing), votre consentement est requis.
                </li>
              </ul>
            </div>
          </section>

          <!-- Article 5 -->
          <section id="destinataires">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 5 - Destinataires des données
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Vos données personnelles peuvent être partagées avec les destinataires suivants :
              </p>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">5.1 Sous-traitants</h3>
              <table class="w-full mt-2">
                <thead>
                  <tr class="bg-gray-100">
                    <th class="text-left p-3 font-semibold">Prestataire</th>
                    <th class="text-left p-3 font-semibold">Service</th>
                    <th class="text-left p-3 font-semibold">Localisation</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b">
                    <td class="p-3">Stripe</td>
                    <td class="p-3">Paiement en ligne</td>
                    <td class="p-3">USA (Privacy Shield)</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Railway</td>
                    <td class="p-3">Hébergement API</td>
                    <td class="p-3">USA</td>
                  </tr>
                  <tr>
                    <td class="p-3">Vercel</td>
                    <td class="p-3">Hébergement frontend</td>
                    <td class="p-3">USA</td>
                  </tr>
                </tbody>
              </table>

              <h3 class="text-lg font-semibold text-secondary-900 mt-6 mb-3">5.2 Autres destinataires</h3>
              <ul>
                <li>Autorités administratives ou judiciaires en cas d'obligation légale</li>
                <li>Marketplaces tierces (Vinted, eBay, Etsy) pour la publication de vos produits, selon vos instructions</li>
              </ul>

              <p class="mt-4">
                <strong>Vos données ne sont jamais vendues à des tiers.</strong>
              </p>
            </div>
          </section>

          <!-- Article 6 -->
          <section id="conservation">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 6 - Durée de conservation
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Vos données personnelles sont conservées pour les durées suivantes :
              </p>
              <table class="w-full mt-4">
                <thead>
                  <tr class="bg-gray-100">
                    <th class="text-left p-3 font-semibold">Type de données</th>
                    <th class="text-left p-3 font-semibold">Durée de conservation</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b">
                    <td class="p-3">Données de compte</td>
                    <td class="p-3">Durée de l'abonnement + 3 ans</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Données de facturation</td>
                    <td class="p-3">10 ans (obligation comptable)</td>
                  </tr>
                  <tr class="border-b">
                    <td class="p-3">Données de connexion</td>
                    <td class="p-3">1 an</td>
                  </tr>
                  <tr>
                    <td class="p-3">Données d'utilisation</td>
                    <td class="p-3">3 ans après suppression du compte</td>
                  </tr>
                </tbody>
              </table>
              <p class="mt-4">
                À l'issue de ces durées, vos données sont supprimées ou anonymisées de manière irréversible.
              </p>
            </div>
          </section>

          <!-- Article 7 -->
          <section id="droits">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 7 - Vos droits
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Conformément au RGPD, vous disposez des droits suivants sur vos données personnelles :
              </p>

              <div class="grid md:grid-cols-2 gap-4 mt-6">
                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-eye text-primary-500" />
                    Droit d'accès
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Obtenir une copie de vos données personnelles.
                  </p>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-pencil text-primary-500" />
                    Droit de rectification
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Corriger des données inexactes ou incomplètes.
                  </p>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-trash text-primary-500" />
                    Droit à l'effacement
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Demander la suppression de vos données (sous conditions).
                  </p>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-download text-primary-500" />
                    Droit à la portabilité
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Récupérer vos données dans un format structuré.
                  </p>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-ban text-primary-500" />
                    Droit d'opposition
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Vous opposer à certains traitements de vos données.
                  </p>
                </div>

                <div class="bg-gray-50 rounded-lg p-4">
                  <h4 class="font-semibold text-secondary-900 flex items-center gap-2">
                    <i class="pi pi-pause text-primary-500" />
                    Droit à la limitation
                  </h4>
                  <p class="text-sm text-gray-600 mt-1">
                    Limiter le traitement de vos données.
                  </p>
                </div>
              </div>

              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                <p class="text-blue-800">
                  <strong>Pour exercer vos droits :</strong> Envoyez un email à
                  <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a>
                  en précisant votre demande et en joignant une copie d'un justificatif d'identité.
                </p>
                <p class="text-blue-700 mt-2 text-sm">
                  Nous vous répondrons dans un délai maximum d'un (1) mois.
                </p>
              </div>

              <p class="mt-6">
                <strong>Réclamation auprès de la CNIL</strong><br>
                Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation
                auprès de la Commission Nationale de l'Informatique et des Libertés (CNIL) :
                <a href="https://www.cnil.fr" target="_blank" rel="noopener" class="text-primary-600 hover:underline">www.cnil.fr</a>
              </p>
            </div>
          </section>

          <!-- Article 8 -->
          <section id="cookies">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 8 - Cookies
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>8.1 Qu'est-ce qu'un cookie ?</strong><br>
                Un cookie est un petit fichier texte déposé sur votre appareil lors de la visite d'un site web.
                Il permet de mémoriser des informations relatives à votre navigation.
              </p>

              <p>
                <strong>8.2 Cookies utilisés par StoFlow</strong><br>
                StoFlow utilise uniquement des <strong>cookies strictement nécessaires</strong> au fonctionnement
                du service :
              </p>

              <table class="w-full mt-4">
                <thead>
                  <tr class="bg-gray-100">
                    <th class="text-left p-3 font-semibold">Nom</th>
                    <th class="text-left p-3 font-semibold">Finalité</th>
                    <th class="text-left p-3 font-semibold">Durée</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b">
                    <td class="p-3 font-mono text-sm">auth_token</td>
                    <td class="p-3">Authentification de l'utilisateur</td>
                    <td class="p-3">Session</td>
                  </tr>
                  <tr>
                    <td class="p-3 font-mono text-sm">refresh_token</td>
                    <td class="p-3">Renouvellement de la session</td>
                    <td class="p-3">7 jours</td>
                  </tr>
                </tbody>
              </table>

              <div class="bg-green-50 border border-green-200 rounded-lg p-4 mt-6">
                <p class="text-green-800 flex items-center gap-2">
                  <i class="pi pi-check-circle" />
                  <strong>Pas de consentement requis</strong>
                </p>
                <p class="text-green-700 mt-2 text-sm">
                  Ces cookies sont exemptés du recueil de consentement car ils sont strictement nécessaires
                  à la fourniture du service (Article 82 de la loi Informatique et Libertés).
                </p>
              </div>

              <p class="mt-4">
                <strong>8.3 Cookies tiers</strong><br>
                StoFlow n'utilise pas de cookies publicitaires, de tracking ou d'analyse comportementale.
              </p>
            </div>
          </section>

          <!-- Article 9 -->
          <section id="securite">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 9 - Sécurité des données
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Stokode SARL met en œuvre des mesures techniques et organisationnelles appropriées pour
                assurer la sécurité de vos données personnelles :
              </p>
              <ul>
                <li>Chiffrement des données en transit (HTTPS/TLS)</li>
                <li>Chiffrement des mots de passe (bcrypt)</li>
                <li>Authentification sécurisée par JWT</li>
                <li>Accès restreint aux données (principe du moindre privilège)</li>
                <li>Sauvegardes régulières</li>
                <li>Surveillance et détection des intrusions</li>
              </ul>
              <p>
                En cas de violation de données susceptible d'engendrer un risque élevé pour vos droits et
                libertés, vous serez informé dans les meilleurs délais conformément à l'article 34 du RGPD.
              </p>
            </div>
          </section>

          <!-- Article 10 -->
          <section id="transferts">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 10 - Transferts de données hors UE
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Certains de nos sous-traitants (Stripe, Railway, Vercel) sont situés aux États-Unis. Ces
                transferts sont encadrés par :
              </p>
              <ul>
                <li>Les clauses contractuelles types (CCT) approuvées par la Commission européenne</li>
                <li>Le Data Privacy Framework (DPF) UE-États-Unis pour les entreprises certifiées</li>
              </ul>
              <p>
                Ces mécanismes garantissent un niveau de protection adéquat de vos données personnelles
                conformément aux exigences du RGPD.
              </p>
            </div>
          </section>

          <!-- Article 11 -->
          <section id="modifications">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 11 - Modifications de la politique
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Stokode SARL se réserve le droit de modifier la présente politique de confidentialité à tout
                moment. En cas de modification substantielle, vous serez informé par email ou par notification
                dans l'interface du service.
              </p>
              <p>
                Nous vous invitons à consulter régulièrement cette page pour prendre connaissance des
                éventuelles modifications.
              </p>
            </div>
          </section>

          <!-- Article 12 -->
          <section id="contact" class="border-t border-gray-200 pt-8">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 12 - Contact
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Pour toute question concernant cette politique de confidentialité ou pour exercer vos droits,
                vous pouvez nous contacter :
              </p>
              <div class="bg-gray-50 rounded-lg p-6 mt-4">
                <p><strong>Email :</strong> <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a></p>
                <p><strong>Adresse :</strong> Stokode SARL, 5 rue Emile Zola, 77340 Pontault-Combault, France</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>

    <LayoutFooterFull />
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

useSeoMeta({
  title: 'Politique de Confidentialité - StoFlow',
  description: 'Politique de confidentialité de StoFlow : protection des données personnelles, cookies et droits RGPD.'
})

const lastUpdate = computed(() => {
  return new Date().toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})
</script>
