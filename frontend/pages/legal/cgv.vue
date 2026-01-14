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
            Conditions Générales de Vente
          </h1>
          <p class="text-gray-500">
            Dernière mise à jour : {{ lastUpdate }}
          </p>
        </div>

        <!-- Table of contents -->
        <div class="bg-primary-50 rounded-xl p-6 mb-8">
          <h2 class="font-bold text-secondary-900 mb-3">Sommaire</h2>
          <ol class="list-decimal list-inside space-y-1 text-gray-700">
            <li><a href="#objet" class="hover:text-primary-600">Objet et champ d'application</a></li>
            <li><a href="#offres" class="hover:text-primary-600">Offres et tarifs</a></li>
            <li><a href="#commande" class="hover:text-primary-600">Commande et paiement</a></li>
            <li><a href="#retractation" class="hover:text-primary-600">Droit de rétractation</a></li>
            <li><a href="#duree" class="hover:text-primary-600">Durée et renouvellement</a></li>
            <li><a href="#resiliation" class="hover:text-primary-600">Résiliation</a></li>
            <li><a href="#garanties" class="hover:text-primary-600">Garanties légales</a></li>
            <li><a href="#responsabilite" class="hover:text-primary-600">Responsabilité</a></li>
            <li><a href="#donnees" class="hover:text-primary-600">Protection des données</a></li>
            <li><a href="#mediation" class="hover:text-primary-600">Médiation et litiges</a></li>
            <li><a href="#droit" class="hover:text-primary-600">Droit applicable</a></li>
          </ol>
        </div>

        <!-- Content -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">
          <!-- Préambule -->
          <section class="bg-gray-50 rounded-lg p-6">
            <p class="text-gray-700">
              <strong>Vendeur :</strong> Stokode SARL, société au capital de 1 000 €, immatriculée au RCS de Melun
              sous le numéro 992 682 393, dont le siège social est situé au 5 rue Emile Zola, 77340 Pontault-Combault, France.
            </p>
            <p class="text-gray-700 mt-2">
              <strong>N° TVA intracommunautaire :</strong> FR42992682393
            </p>
            <p class="text-gray-700 mt-2">
              <strong>Contact :</strong> <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a>
            </p>
          </section>

          <!-- Article 1 -->
          <section id="objet">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 1 - Objet et champ d'application
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Les présentes Conditions Générales de Vente (ci-après « CGV ») régissent les relations contractuelles
                entre Stokode SARL (ci-après « le Vendeur ») et toute personne physique ou morale (ci-après « le Client »)
                souhaitant souscrire à un abonnement au service StoFlow.
              </p>
              <p>
                Toute souscription à un abonnement implique l'acceptation sans réserve des présentes CGV, qui prévalent
                sur tout autre document.
              </p>
              <p>
                Le Vendeur se réserve le droit de modifier les présentes CGV à tout moment. Les CGV applicables sont
                celles en vigueur à la date de la commande.
              </p>
            </div>
          </section>

          <!-- Article 2 -->
          <section id="offres">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 2 - Offres et tarifs
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>2.1 Description des offres</strong><br>
                Le Vendeur propose différentes formules d'abonnement au service StoFlow. Le détail des fonctionnalités
                et des tarifs de chaque formule est disponible sur la
                <NuxtLink to="/#pricing" class="text-primary-600 hover:underline">page des tarifs</NuxtLink> du site.
              </p>
              <p>
                <strong>2.2 Prix</strong><br>
                Les prix sont indiqués en euros, toutes taxes comprises (TTC). Le Vendeur se réserve le droit de
                modifier ses prix à tout moment. Les modifications de prix ne s'appliquent pas aux abonnements en cours.
              </p>
              <p>
                <strong>2.3 Crédits IA</strong><br>
                Certaines formules incluent des crédits d'Intelligence Artificielle (IA) permettant d'utiliser les
                fonctionnalités d'optimisation automatique. Ces crédits sont renouvelés mensuellement et ne sont pas
                reportables d'un mois sur l'autre.
              </p>
            </div>
          </section>

          <!-- Article 3 -->
          <section id="commande">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 3 - Commande et paiement
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>3.1 Processus de commande</strong><br>
                Pour souscrire à un abonnement, le Client doit :
              </p>
              <ol>
                <li>Créer un compte utilisateur ou se connecter à son compte existant</li>
                <li>Choisir la formule d'abonnement souhaitée (mensuelle ou annuelle)</li>
                <li>Renseigner ses informations de facturation</li>
                <li>Accepter les présentes CGV et la Politique de Confidentialité</li>
                <li>Procéder au paiement</li>
              </ol>
              <p>
                La commande est définitive après validation du paiement. Un email de confirmation est envoyé au Client.
              </p>
              <p>
                <strong>3.2 Moyens de paiement</strong><br>
                Le paiement s'effectue par carte bancaire via la plateforme sécurisée Stripe. Les données bancaires
                du Client sont directement transmises à Stripe et ne sont jamais stockées par le Vendeur.
              </p>
              <p>
                <strong>3.3 Sécurité des paiements</strong><br>
                Stripe est certifié PCI-DSS niveau 1, garantissant le plus haut niveau de sécurité pour les
                transactions par carte bancaire.
              </p>
              <p>
                <strong>3.4 Facturation</strong><br>
                Une facture est émise et envoyée par email au Client après chaque paiement. Les factures sont
                également accessibles dans l'espace client.
              </p>
            </div>
          </section>

          <!-- Article 4 - DROIT DE RÉTRACTATION -->
          <section id="retractation">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 4 - Droit de rétractation
            </h2>

            <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <p class="text-amber-800 font-medium flex items-center gap-2">
                <i class="pi pi-info-circle" />
                Information importante sur votre droit de rétractation
              </p>
            </div>

            <div class="prose prose-gray max-w-none">
              <p>
                <strong>4.1 Délai de rétractation</strong><br>
                Conformément aux articles L221-18 et suivants du Code de la consommation, le Client consommateur
                dispose d'un délai de <strong>quatorze (14) jours</strong> à compter de la souscription de l'abonnement
                pour exercer son droit de rétractation, sans avoir à justifier de motifs ni à payer de pénalités.
              </p>

              <p>
                <strong>4.2 Exercice du droit de rétractation</strong><br>
                Pour exercer son droit de rétractation, le Client doit notifier sa décision de rétractation au moyen
                d'une déclaration dénuée d'ambiguïté, par email à
                <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a>
                ou en utilisant le formulaire de rétractation ci-dessous.
              </p>

              <p>
                <strong>4.3 Remboursement</strong><br>
                En cas de rétractation, le Vendeur rembourse le Client de la totalité des sommes versées, au plus
                tard dans les quatorze (14) jours suivant la réception de la demande de rétractation.
              </p>
              <p>
                Le remboursement est effectué en utilisant le même moyen de paiement que celui utilisé pour la
                transaction initiale, sauf accord exprès du Client pour un autre moyen.
              </p>

              <div class="bg-red-50 border border-red-200 rounded-lg p-4 my-4">
                <p class="text-red-800 font-medium flex items-center gap-2 mb-2">
                  <i class="pi pi-exclamation-triangle" />
                  Exception pour les crédits IA utilisés
                </p>
                <p class="text-red-700 text-sm">
                  <strong>4.4 Renonciation partielle au droit de rétractation (Article L221-28 du Code de la consommation)</strong><br><br>
                  L'utilisation des crédits IA constitue la fourniture d'un contenu numérique non fourni sur un support
                  matériel dont l'exécution commence immédiatement.<br><br>
                  <strong>En utilisant les crédits IA, le Client reconnaît expressément :</strong>
                </p>
                <ul class="text-red-700 text-sm list-disc list-inside mt-2 space-y-1">
                  <li>Avoir demandé l'exécution immédiate du service</li>
                  <li>Renoncer à son droit de rétractation pour les crédits IA déjà utilisés</li>
                </ul>
                <p class="text-red-700 text-sm mt-2">
                  En cas de rétractation, <strong>les crédits IA utilisés ne seront pas remboursés</strong>. Seule la partie
                  de l'abonnement correspondant aux crédits non utilisés sera remboursée.
                </p>
              </div>

              <!-- Formulaire de rétractation -->
              <div class="bg-gray-100 rounded-lg p-6 mt-6">
                <h3 class="font-bold text-secondary-900 mb-4">Formulaire de rétractation</h3>
                <p class="text-sm text-gray-600 mb-4">
                  (Veuillez compléter et renvoyer le présent formulaire uniquement si vous souhaitez vous rétracter du contrat)
                </p>
                <div class="bg-white rounded-lg p-4 text-sm">
                  <p>À l'attention de Stokode SARL,</p>
                  <p>5 rue Emile Zola, 77340 Pontault-Combault, France</p>
                  <p>Email : contact@stoflow.io</p>
                  <br>
                  <p>Je vous notifie par la présente ma rétractation du contrat portant sur la vente du service ci-dessous :</p>
                  <br>
                  <p>- Formule d'abonnement : ________________</p>
                  <p>- Commandé le : ________________</p>
                  <p>- Nom du consommateur : ________________</p>
                  <p>- Adresse du consommateur : ________________</p>
                  <p>- Email du consommateur : ________________</p>
                  <br>
                  <p>Date : ________________</p>
                  <p>Signature (en cas de notification sur papier) : ________________</p>
                </div>
              </div>
            </div>
          </section>

          <!-- Article 5 -->
          <section id="duree">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 5 - Durée et renouvellement
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>5.1 Durée de l'abonnement</strong><br>
                L'abonnement est souscrit pour une durée d'un (1) mois ou d'un (1) an, selon la formule choisie
                par le Client.
              </p>
              <p>
                <strong>5.2 Renouvellement automatique</strong><br>
                L'abonnement est renouvelé automatiquement à chaque échéance pour une durée identique, sauf
                résiliation par le Client avant la date de renouvellement.
              </p>
              <p>
                Le Client sera informé par email de l'échéance de son abonnement au moins sept (7) jours avant
                la date de renouvellement.
              </p>
            </div>
          </section>

          <!-- Article 6 -->
          <section id="resiliation">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 6 - Résiliation
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>6.1 Résiliation par le Client</strong><br>
                Le Client peut résilier son abonnement à tout moment depuis son espace client ou en contactant
                le support à <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a>.
              </p>
              <p>
                <strong>La résiliation prend effet à la fin de la période d'abonnement en cours.</strong> Le Client
                conserve l'accès au service jusqu'à cette date. Aucun remboursement au prorata n'est effectué.
              </p>
              <p>
                <strong>6.2 Résiliation par le Vendeur</strong><br>
                Le Vendeur peut résilier l'abonnement du Client de plein droit et sans préavis en cas de :
              </p>
              <ul>
                <li>Non-paiement d'une échéance</li>
                <li>Violation des Conditions Générales d'Utilisation</li>
                <li>Utilisation frauduleuse du service</li>
              </ul>
              <p>
                <strong>6.3 Conséquences de la résiliation</strong><br>
                À la date de résiliation, le compte du Client est désactivé et ses données sont traitées
                conformément à notre Politique de Confidentialité.
              </p>
            </div>
          </section>

          <!-- Article 7 -->
          <section id="garanties">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 7 - Garanties légales
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Le Client bénéficie des garanties légales prévues par le Code de la consommation, notamment :
              </p>
              <p>
                <strong>7.1 Garantie légale de conformité (Articles L217-4 à L217-14)</strong><br>
                Le Vendeur est tenu de livrer un service conforme au contrat et répond des défauts de conformité
                existant lors de la délivrance.
              </p>
              <p>
                <strong>7.2 Garantie des vices cachés (Articles 1641 à 1649 du Code civil)</strong><br>
                Le Vendeur est tenu de la garantie à raison des défauts cachés du service vendu qui le rendent
                impropre à l'usage auquel on le destine.
              </p>
            </div>
          </section>

          <!-- Article 8 -->
          <section id="responsabilite">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 8 - Responsabilité
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>8.1 Limitation de responsabilité</strong><br>
                Le Vendeur ne saurait être tenu responsable des dommages indirects, tels que perte de profits,
                perte de données, perte de clientèle, préjudice commercial, résultant de l'utilisation du service.
              </p>
              <p>
                <strong>8.2 Plafond de responsabilité</strong><br>
                En tout état de cause, la responsabilité du Vendeur est limitée au montant des sommes effectivement
                versées par le Client au titre de son abonnement au cours des douze (12) mois précédant le fait
                générateur du dommage.
              </p>
              <p>
                <strong>8.3 Force majeure</strong><br>
                Le Vendeur ne saurait être tenu responsable de l'inexécution de ses obligations en cas de force
                majeure telle que définie par la jurisprudence française.
              </p>
            </div>
          </section>

          <!-- Article 9 -->
          <section id="donnees">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 9 - Protection des données personnelles
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Le Vendeur s'engage à protéger les données personnelles du Client conformément au Règlement Général
                sur la Protection des Données (RGPD) et à la loi Informatique et Libertés.
              </p>
              <p>
                Pour plus d'informations sur le traitement de vos données personnelles, consultez notre
                <NuxtLink to="/legal/privacy" class="text-primary-600 hover:underline">Politique de Confidentialité</NuxtLink>.
              </p>
            </div>
          </section>

          <!-- Article 10 -->
          <section id="mediation">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 10 - Médiation et litiges
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>10.1 Réclamation préalable</strong><br>
                En cas de litige, le Client est invité à contacter en premier lieu le service client du Vendeur
                à l'adresse <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a>.
              </p>
              <p>
                <strong>10.2 Plateforme européenne de règlement en ligne des litiges</strong><br>
                Le Client peut utiliser la plateforme de Règlement en Ligne des Litiges (RLL) mise en
                place par la Commission européenne :
                <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener" class="text-primary-600 hover:underline">
                  https://ec.europa.eu/consumers/odr
                </a>
              </p>
            </div>
          </section>

          <!-- Article 11 -->
          <section id="droit">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 11 - Droit applicable
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Les présentes CGV sont régies par le droit français.
              </p>
              <p>
                En cas de litige, et après échec de toute tentative de recherche d'une solution amiable, les
                tribunaux français seront seuls compétents pour connaître de ce litige.
              </p>
              <p>
                Pour les consommateurs résidant dans l'Union européenne, les dispositions impératives de la loi
                du pays de résidence du consommateur s'appliquent si elles sont plus protectrices.
              </p>
            </div>
          </section>

          <!-- Contact -->
          <section class="border-t border-gray-200 pt-8">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Contact
            </h2>
            <p class="text-gray-600">
              Pour toute question concernant les présentes CGV, vous pouvez nous contacter à l'adresse :
              <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline font-medium">contact@stoflow.io</a>
            </p>
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
  title: 'Conditions Générales de Vente (CGV) - StoFlow',
  description: 'CGV de StoFlow : tarifs, paiement, droit de rétractation, résiliation et conditions d\'abonnement.'
})

// Breadcrumb Schema
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Informations légales', url: '/legal' },
  { name: 'Conditions générales de vente', url: '/legal/cgv' }
])

const lastUpdate = computed(() => {
  return new Date().toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})
</script>
