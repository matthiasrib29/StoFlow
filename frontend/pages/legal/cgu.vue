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
            Conditions Générales d'Utilisation
          </h1>
          <p class="text-gray-500">
            Dernière mise à jour : {{ lastUpdate }}
          </p>
        </div>

        <!-- Table of contents -->
        <div class="bg-blue-50 rounded-xl p-6 mb-8">
          <h2 class="font-bold text-secondary-900 mb-3">Sommaire</h2>
          <ol class="list-decimal list-inside space-y-1 text-gray-700">
            <li><a href="#objet" class="hover:text-primary-600">Objet</a></li>
            <li><a href="#acces" class="hover:text-primary-600">Accès au service</a></li>
            <li><a href="#description" class="hover:text-primary-600">Description du service</a></li>
            <li><a href="#inscription" class="hover:text-primary-600">Inscription et compte utilisateur</a></li>
            <li><a href="#obligations" class="hover:text-primary-600">Obligations de l'utilisateur</a></li>
            <li><a href="#propriete" class="hover:text-primary-600">Propriété intellectuelle</a></li>
            <li><a href="#donnees" class="hover:text-primary-600">Données personnelles</a></li>
            <li><a href="#responsabilite" class="hover:text-primary-600">Responsabilité</a></li>
            <li><a href="#modification" class="hover:text-primary-600">Modification des CGU</a></li>
            <li><a href="#droit" class="hover:text-primary-600">Droit applicable</a></li>
          </ol>
        </div>

        <!-- Content -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">
          <!-- Article 1 -->
          <section id="objet">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 1 - Objet
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Les présentes Conditions Générales d'Utilisation (ci-après « CGU ») ont pour objet de définir les
                modalités et conditions d'utilisation du service StoFlow (ci-après « le Service »), ainsi que de
                définir les droits et obligations des parties dans ce cadre.
              </p>
              <p>
                Elles sont accessibles et imprimables à tout moment par un lien direct en bas de page du site.
              </p>
              <p>
                Elles peuvent être complétées, le cas échéant, par des conditions d'utilisation particulières à
                certains services. En cas de contradiction, les conditions particulières prévalent sur les présentes CGU.
              </p>
            </div>
          </section>

          <!-- Article 2 -->
          <section id="acces">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 2 - Accès au service
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Le Service est accessible gratuitement en tout lieu à tout utilisateur ayant un accès à Internet.
                Tous les frais supportés par l'utilisateur pour accéder au service (matériel informatique, logiciels,
                connexion Internet, etc.) sont à sa charge.
              </p>
              <p>
                L'utilisateur non-membre n'a pas accès aux services réservés. Pour cela, il doit créer un compte
                utilisateur en remplissant le formulaire d'inscription.
              </p>
              <p>
                Stokode SARL met en œuvre tous les moyens raisonnables à sa disposition pour assurer un accès de
                qualité au Service, mais n'est tenue à aucune obligation d'y parvenir.
              </p>
              <p>
                Stokode SARL ne peut, en outre, être tenue responsable de tout dysfonctionnement du réseau ou des
                serveurs ou de tout autre événement échappant au contrôle raisonnable, qui empêcherait ou dégraderait
                l'accès au Service.
              </p>
              <p>
                Stokode SARL se réserve la possibilité d'interrompre, de suspendre momentanément ou de modifier sans
                préavis l'accès à tout ou partie du Service, afin d'en assurer la maintenance, ou pour toute autre
                raison, sans que l'interruption n'ouvre droit à aucune obligation ni indemnisation.
              </p>
            </div>
          </section>

          <!-- Article 3 -->
          <section id="description">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 3 - Description du service
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                StoFlow est une plateforme SaaS (Software as a Service) de gestion e-commerce multi-marketplace
                permettant aux utilisateurs de :
              </p>
              <ul>
                <li>Centraliser la gestion de leurs produits depuis une interface unique</li>
                <li>Publier leurs produits sur différentes marketplaces (Vinted, eBay, Etsy, etc.)</li>
                <li>Synchroniser automatiquement leurs stocks et prix</li>
                <li>Gérer leurs commandes et expéditions</li>
                <li>Utiliser des outils d'intelligence artificielle pour optimiser leurs annonces</li>
                <li>Suivre leurs performances de vente</li>
              </ul>
              <p>
                Les fonctionnalités disponibles dépendent de la formule d'abonnement souscrite par l'utilisateur.
                Le détail des fonctionnalités est disponible sur la page des tarifs du site.
              </p>
            </div>
          </section>

          <!-- Article 4 -->
          <section id="inscription">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 4 - Inscription et compte utilisateur
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>4.1 Création de compte</strong><br>
                L'utilisation du Service nécessite la création d'un compte utilisateur. L'utilisateur doit fournir
                des informations exactes et complètes lors de son inscription, notamment :
              </p>
              <ul>
                <li>Nom et prénom</li>
                <li>Adresse email valide</li>
                <li>Mot de passe sécurisé</li>
              </ul>
              <p>
                <strong>4.2 Sécurité du compte</strong><br>
                L'utilisateur est seul responsable de la préservation de la confidentialité de ses identifiants
                de connexion. Toute utilisation du Service effectuée à partir de son compte sera réputée avoir
                été effectuée par lui.
              </p>
              <p>
                En cas de perte, de vol ou d'utilisation frauduleuse de ses identifiants, l'utilisateur doit
                immédiatement en informer Stokode SARL à l'adresse contact@stoflow.io.
              </p>
              <p>
                <strong>4.3 Suppression de compte</strong><br>
                L'utilisateur peut à tout moment demander la suppression de son compte en contactant le support
                ou via les paramètres de son compte. La suppression entraîne la perte définitive de toutes les
                données associées au compte, sous réserve des obligations légales de conservation.
              </p>
            </div>
          </section>

          <!-- Article 5 -->
          <section id="obligations">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 5 - Obligations de l'utilisateur
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                L'utilisateur s'engage à utiliser le Service de manière conforme aux présentes CGU et à la
                réglementation en vigueur. Il s'interdit notamment de :
              </p>
              <ul>
                <li>Utiliser le Service à des fins illégales ou contraires aux bonnes mœurs</li>
                <li>Diffuser des contenus illicites, diffamatoires, injurieux ou portant atteinte aux droits de tiers</li>
                <li>Tenter d'accéder frauduleusement aux systèmes informatiques de Stokode SARL</li>
                <li>Utiliser des robots, scripts ou autres moyens automatisés non autorisés</li>
                <li>Revendre, céder ou transférer son compte à un tiers sans autorisation</li>
                <li>Contourner les limitations techniques du Service</li>
                <li>Utiliser le Service pour envoyer des communications non sollicitées (spam)</li>
              </ul>
              <p>
                En cas de manquement à ces obligations, Stokode SARL se réserve le droit de suspendre ou de
                résilier l'accès au Service sans préavis ni indemnité.
              </p>
            </div>
          </section>

          <!-- Article 6 -->
          <section id="propriete">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 6 - Propriété intellectuelle
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                <strong>6.1 Droits de Stokode SARL</strong><br>
                L'ensemble des éléments constituant le Service (logiciels, bases de données, textes, images,
                graphismes, logos, etc.) est la propriété exclusive de Stokode SARL et est protégé par les lois
                relatives à la propriété intellectuelle.
              </p>
              <p>
                Toute reproduction, représentation, modification ou exploitation non autorisée de ces éléments
                est strictement interdite et constitue une contrefaçon.
              </p>
              <p>
                <strong>6.2 Contenus de l'utilisateur</strong><br>
                L'utilisateur conserve l'intégralité de ses droits de propriété intellectuelle sur les contenus
                qu'il publie via le Service (descriptions de produits, images, etc.).
              </p>
              <p>
                En utilisant le Service, l'utilisateur accorde à Stokode SARL une licence non exclusive, mondiale
                et gratuite d'utilisation de ces contenus, dans le seul but de fournir le Service (affichage,
                publication sur les marketplaces, etc.).
              </p>
            </div>
          </section>

          <!-- Article 7 -->
          <section id="donnees">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 7 - Données personnelles
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Dans le cadre de l'utilisation du Service, Stokode SARL est amenée à collecter et traiter des
                données personnelles de l'utilisateur.
              </p>
              <p>
                L'utilisateur est invité à consulter la
                <NuxtLink to="/legal/privacy" class="text-primary-600 hover:underline">Politique de Confidentialité</NuxtLink>
                pour connaître les modalités de collecte, de traitement et de protection de ses données personnelles.
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
                <strong>8.1 Responsabilité de Stokode SARL</strong><br>
                Stokode SARL s'engage à mettre en œuvre tous les moyens nécessaires pour assurer la continuité
                et la qualité du Service. Toutefois, sa responsabilité ne saurait être engagée en cas de :
              </p>
              <ul>
                <li>Force majeure ou fait d'un tiers</li>
                <li>Dysfonctionnement des réseaux de communication</li>
                <li>Indisponibilité temporaire du Service pour maintenance</li>
                <li>Utilisation non conforme du Service par l'utilisateur</li>
                <li>Fait des marketplaces tierces (Vinted, eBay, Etsy, etc.)</li>
              </ul>
              <p>
                <strong>8.2 Limitation de responsabilité</strong><br>
                En tout état de cause, la responsabilité de Stokode SARL ne pourra être engagée qu'en cas de
                faute prouvée et sera limitée aux dommages directs, à l'exclusion de tout dommage indirect.
              </p>
              <p>
                La responsabilité de Stokode SARL est limitée au montant des sommes effectivement versées par
                l'utilisateur au cours des douze (12) mois précédant le fait générateur du dommage.
              </p>
            </div>
          </section>

          <!-- Article 9 -->
          <section id="modification">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 9 - Modification des CGU
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Stokode SARL se réserve le droit de modifier les présentes CGU à tout moment. Les utilisateurs
                seront informés de toute modification par email ou par notification dans l'interface du Service.
              </p>
              <p>
                Les nouvelles CGU entreront en vigueur trente (30) jours après leur notification. L'utilisation
                continue du Service après cette période vaut acceptation des nouvelles CGU.
              </p>
              <p>
                Si l'utilisateur n'accepte pas les nouvelles CGU, il peut résilier son compte avant leur entrée
                en vigueur.
              </p>
            </div>
          </section>

          <!-- Article 10 -->
          <section id="droit">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Article 10 - Droit applicable et litiges
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Les présentes CGU sont régies par le droit français.
              </p>
              <p>
                En cas de litige relatif à l'interprétation ou à l'exécution des présentes CGU, les parties
                s'efforceront de trouver une solution amiable.
              </p>
              <p>
                À défaut d'accord amiable, tout litige sera soumis aux tribunaux compétents du ressort de la
                Cour d'appel de Paris.
              </p>
            </div>
          </section>

          <!-- Contact -->
          <section class="border-t border-gray-200 pt-8">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4">
              Contact
            </h2>
            <p class="text-gray-600">
              Pour toute question concernant les présentes CGU, vous pouvez nous contacter à l'adresse :
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
  title: 'Conditions Générales d\'Utilisation (CGU) - StoFlow',
  description: 'CGU de StoFlow : règles d\'utilisation du service, droits et obligations des utilisateurs.'
})

// Breadcrumb Schema
useBreadcrumbSchema([
  { name: 'Accueil', url: '/' },
  { name: 'Informations légales', url: '/legal' },
  { name: 'Conditions générales d\'utilisation', url: '/legal/cgu' }
])

const lastUpdate = computed(() => {
  return new Date().toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})
</script>
