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
            Mentions Légales
          </h1>
          <p class="text-gray-500">
            Dernière mise à jour : {{ lastUpdate }}
          </p>
        </div>

        <!-- Content -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">
          <!-- Éditeur du site -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-building text-primary-500" />
              Éditeur du site
            </h2>
            <div class="bg-gray-50 rounded-lg p-6 space-y-3">
              <p><strong>Raison sociale :</strong> Stokode SARL</p>
              <p><strong>Nom commercial :</strong> StoFlow</p>
              <p><strong>Forme juridique :</strong> Société à Responsabilité Limitée (SARL)</p>
              <p><strong>Capital social :</strong> 1 000 €</p>
              <p><strong>Siège social :</strong> 5 rue Emile Zola, 77340 Pontault-Combault, France</p>
              <p><strong>SIRET :</strong> 992 682 393 00010</p>
              <p><strong>RCS :</strong> Melun</p>
              <p><strong>N° TVA intracommunautaire :</strong> FR42992682393</p>
              <p><strong>Email :</strong> <a href="mailto:contact@stoflow.io" class="text-primary-600 hover:underline">contact@stoflow.io</a></p>
            </div>
          </section>

          <!-- Directeur de publication -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-user text-primary-500" />
              Directeur de la publication
            </h2>
            <div class="bg-gray-50 rounded-lg p-6">
              <p><strong>Nom :</strong> Matthias Ribeiro</p>
              <p><strong>Qualité :</strong> Gérant de Stokode SARL</p>
            </div>
          </section>

          <!-- Hébergement -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-server text-primary-500" />
              Hébergement
            </h2>
            <div class="space-y-4">
              <div class="bg-gray-50 rounded-lg p-6">
                <p class="font-semibold text-secondary-900 mb-2">Site web (Frontend)</p>
                <p><strong>Hébergeur :</strong> Vercel Inc.</p>
                <p><strong>Adresse :</strong> 440 N Barranca Ave #4133, Covina, CA 91723, États-Unis</p>
                <p><strong>Site web :</strong> <a href="https://vercel.com" target="_blank" rel="noopener" class="text-primary-600 hover:underline">vercel.com</a></p>
              </div>
              <div class="bg-gray-50 rounded-lg p-6">
                <p class="font-semibold text-secondary-900 mb-2">API (Backend)</p>
                <p><strong>Hébergeur :</strong> Railway Corporation</p>
                <p><strong>Adresse :</strong> 548 Market St, PMB 63795, San Francisco, CA 94104, États-Unis</p>
                <p><strong>Site web :</strong> <a href="https://railway.app" target="_blank" rel="noopener" class="text-primary-600 hover:underline">railway.app</a></p>
              </div>
            </div>
          </section>

          <!-- Propriété intellectuelle -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-verified text-primary-500" />
              Propriété intellectuelle
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                L'ensemble du contenu du site StoFlow (textes, images, graphismes, logo, icônes, sons, logiciels, etc.)
                est la propriété exclusive de Stokode SARL ou de ses partenaires et est protégé par les lois françaises
                et internationales relatives à la propriété intellectuelle.
              </p>
              <p>
                Toute reproduction, représentation, modification, publication, adaptation de tout ou partie des éléments
                du site, quel que soit le moyen ou le procédé utilisé, est interdite, sauf autorisation écrite préalable de Stokode SARL.
              </p>
              <p>
                Toute exploitation non autorisée du site ou de l'un quelconque des éléments qu'il contient sera considérée
                comme constitutive d'une contrefaçon et poursuivie conformément aux dispositions des articles L.335-2 et
                suivants du Code de Propriété Intellectuelle.
              </p>
            </div>
          </section>

          <!-- Liens hypertextes -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-link text-primary-500" />
              Liens hypertextes
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Le site StoFlow peut contenir des liens hypertextes vers d'autres sites internet. Stokode SARL n'exerce
                aucun contrôle sur ces sites et décline toute responsabilité quant à leur contenu.
              </p>
              <p>
                La création de liens hypertextes vers le site StoFlow est soumise à l'accord préalable de Stokode SARL.
              </p>
            </div>
          </section>

          <!-- Limitation de responsabilité -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-exclamation-triangle text-primary-500" />
              Limitation de responsabilité
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Stokode SARL s'efforce d'assurer au mieux de ses possibilités l'exactitude et la mise à jour des informations
                diffusées sur le site StoFlow. Toutefois, Stokode SARL ne peut garantir l'exactitude, la précision ou
                l'exhaustivité des informations mises à disposition sur ce site.
              </p>
              <p>
                Stokode SARL décline toute responsabilité pour toute imprécision, inexactitude ou omission portant sur
                des informations disponibles sur le site, ainsi que pour tous dommages résultant d'une intrusion frauduleuse
                d'un tiers ayant entraîné une modification des informations mises à disposition sur le site.
              </p>
            </div>
          </section>

          <!-- Droit applicable -->
          <section>
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-balance-scale text-primary-500" />
              Droit applicable
            </h2>
            <div class="prose prose-gray max-w-none">
              <p>
                Les présentes mentions légales sont régies par le droit français. En cas de litige, et après échec de
                toute tentative de recherche d'une solution amiable, les tribunaux français seront seuls compétents
                pour connaître de ce litige.
              </p>
            </div>
          </section>

          <!-- Contact -->
          <section class="border-t border-gray-200 pt-8">
            <h2 class="text-2xl font-bold text-secondary-900 mb-4 flex items-center gap-2">
              <i class="pi pi-envelope text-primary-500" />
              Contact
            </h2>
            <p class="text-gray-600">
              Pour toute question concernant ces mentions légales, vous pouvez nous contacter à l'adresse :
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
  title: 'Mentions Légales - StoFlow',
  description: 'Mentions légales de StoFlow : éditeur, hébergeur, propriété intellectuelle et informations légales obligatoires.'
})

const lastUpdate = computed(() => {
  return new Date().toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})
</script>
