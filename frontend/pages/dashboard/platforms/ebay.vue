<template>
  <div class="p-8">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-white flex items-center justify-center shadow-lg border border-gray-100 p-2">
            <img src="/images/platforms/ebay-logo.png" alt="eBay" class="w-full h-full object-contain" />
          </div>
          <div>
            <h1 class="text-3xl font-bold text-secondary-900 mb-1">eBay</h1>
            <div class="flex items-center gap-3">
              <Badge
                :value="ebayStore.isConnected ? 'Connecté' : 'Déconnecté'"
                :severity="ebayStore.isConnected ? 'success' : 'secondary'"
              />
              <Badge
                v-if="ebayStore.account"
                :value="ebayStore.sellerLevelLabel"
                severity="info"
              />
            </div>
          </div>
        </div>
        <div class="flex gap-3">
          <Button
            label="Retour"
            icon="pi pi-arrow-left"
            class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
            @click="$router.push('/dashboard/platforms')"
          />
          <Button
            v-if="!ebayStore.isConnected"
            label="Connecter eBay"
            icon="pi pi-link"
            class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold"
            :loading="ebayStore.isConnecting"
            @click="handleConnect"
          />
          <template v-else>
            <Button
              icon="pi pi-refresh"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0"
              :loading="ebayStore.isSyncing"
              v-tooltip.bottom="'Synchroniser'"
              @click="handleSync"
            />
            <Button
              label="Déconnecter"
              icon="pi pi-sign-out"
              class="bg-red-500 hover:bg-red-600 text-white border-0 font-semibold"
              severity="danger"
              @click="handleDisconnect"
            />
          </template>
        </div>
      </div>

      <!-- Sync Status Bar -->
      <div v-if="ebayStore.isConnected && ebayStore.syncSettings.lastSyncAt" class="flex items-center gap-2 text-sm text-gray-600">
        <i class="pi pi-clock"></i>
        <span>Dernière synchronisation: {{ formatRelativeTime(ebayStore.syncSettings.lastSyncAt) }}</span>
        <span v-if="ebayStore.isSyncing" class="text-primary-600 font-medium">
          <i class="pi pi-spin pi-spinner mr-1"></i>Synchronisation en cours...
        </span>
      </div>
    </div>

    <!-- Non connecté: Message de connexion -->
    <Card v-if="!ebayStore.isConnected" class="shadow-lg modern-rounded border-0">
      <template #content>
        <div class="text-center py-12">
          <div class="w-24 h-24 mx-auto mb-6 rounded-full bg-blue-100 flex items-center justify-center">
            <i class="pi pi-link text-blue-500 text-5xl"></i>
          </div>
          <h2 class="text-2xl font-bold text-secondary-900 mb-3">Connectez votre compte eBay</h2>
          <p class="text-gray-600 mb-6 max-w-md mx-auto">
            Liez votre compte eBay pour publier vos produits, gérer votre boutique et synchroniser vos ventes automatiquement.
          </p>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-send text-blue-500 text-2xl mb-2"></i>
              <h4 class="font-semibold text-secondary-900 mb-1">Publication facile</h4>
              <p class="text-sm text-gray-600">Publiez vos produits en un clic</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-sync text-blue-500 text-2xl mb-2"></i>
              <h4 class="font-semibold text-secondary-900 mb-1">Sync automatique</h4>
              <p class="text-sm text-gray-600">Stock et prix toujours à jour</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50">
              <i class="pi pi-chart-line text-blue-500 text-2xl mb-2"></i>
              <h4 class="font-semibold text-secondary-900 mb-1">Statistiques</h4>
              <p class="text-sm text-gray-600">Analysez vos performances</p>
            </div>
          </div>

          <Button
            label="Connecter avec eBay"
            icon="pi pi-external-link"
            class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold px-8 py-3"
            :loading="ebayStore.isConnecting"
            @click="handleConnect"
          />

          <p class="text-xs text-gray-500 mt-4">
            En connectant votre compte, vous acceptez les conditions d'utilisation d'eBay
          </p>
        </div>
      </template>
    </Card>

    <!-- Connecté: Contenu principal -->
    <template v-else>
      <!-- Stats Overview -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <i class="pi pi-send text-blue-600 text-lg"></i>
            </div>
            <span class="text-xs text-green-600 font-medium">+5 ce mois</span>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.activeLis }}</h3>
          <p class="text-xs text-gray-600">Annonces actives</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
              <i class="pi pi-eye text-purple-600 text-lg"></i>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatNumber(ebayStore.stats.totalViews) }}</h3>
          <p class="text-xs text-gray-600">Vues totales</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
              <i class="pi pi-check-circle text-green-600 text-lg"></i>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ ebayStore.stats.totalSales }}</h3>
          <p class="text-xs text-gray-600">Ventes</p>
        </div>

        <div class="stat-card bg-white rounded-2xl p-5 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
              <i class="pi pi-euro text-primary-600 text-lg"></i>
            </div>
          </div>
          <h3 class="text-2xl font-bold text-secondary-900 mb-1">{{ formatCurrency(ebayStore.stats.totalRevenue) }}</h3>
          <p class="text-xs text-gray-600">Chiffre d'affaires</p>
        </div>
      </div>

      <!-- Tabs - PrimeVue v4 -->
      <Tabs v-model:value="activeTab" class="ebay-tabs">
        <TabList>
          <Tab value="0">Boutique</Tab>
          <Tab value="1">Publications</Tab>
          <Tab value="2">Politiques</Tab>
          <Tab value="3">Catégories</Tab>
          <Tab value="4">Paramètres</Tab>
        </TabList>
        <TabPanels>
          <!-- Onglet: Boutique -->
          <TabPanel value="0">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Profil Vendeur -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <div class="flex items-center gap-4 mb-6">
                  <div class="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-2xl font-bold">
                    {{ ebayStore.account?.username?.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <h3 class="text-xl font-bold text-secondary-900">
                      {{ ebayStore.account?.businessName || `${ebayStore.account?.firstName || ''} ${ebayStore.account?.lastName || ''}`.trim() || ebayStore.account?.username || 'Compte eBay' }}
                    </h3>
                    <p class="text-sm text-gray-600">@{{ ebayStore.account?.username }}</p>
                    <p class="text-sm text-gray-600">{{ ebayStore.account?.email || 'Email non disponible' }}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <Badge v-if="ebayStore.account?.accountType === 'BUSINESS'" value="Compte Pro" severity="info" />
                      <Badge v-if="ebayStore.account?.sandboxMode" value="Mode Test" severity="warning" />
                    </div>
                  </div>
                </div>

                <Divider />

                <div class="space-y-4">
                  <!-- Feedback Score -->
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Score feedback</span>
                    <div class="flex items-center gap-2">
                      <span class="font-semibold text-secondary-900">{{ ebayStore.account?.feedbackScore || 0 }}</span>
                      <Badge :value="`${ebayStore.account?.feedbackPercentage || 0}%`" severity="success" />
                    </div>
                  </div>

                  <!-- Seller Level -->
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Niveau vendeur</span>
                    <Badge :value="ebayStore.sellerLevelLabel" :severity="getSellerLevelSeverity()" />
                  </div>

                  <!-- Registration Date -->
                  <div v-if="ebayStore.account?.registrationDate" class="flex items-center justify-between">
                    <span class="text-gray-600">Membre depuis</span>
                    <span class="font-semibold text-secondary-900">{{ formatDate(ebayStore.account.registrationDate) }}</span>
                  </div>

                  <div v-if="ebayStore.account?.phone" class="flex items-center justify-between">
                    <span class="text-gray-600">Téléphone</span>
                    <span class="font-semibold text-secondary-900">{{ ebayStore.account.phone }}</span>
                  </div>
                  <div v-if="ebayStore.account?.address" class="flex items-start justify-between">
                    <span class="text-gray-600">Adresse</span>
                    <span class="font-semibold text-secondary-900 text-right max-w-xs">{{ ebayStore.account.address }}</span>
                  </div>
                  <div v-if="ebayStore.account?.marketplace" class="flex items-center justify-between">
                    <span class="text-gray-600">Marketplace</span>
                    <span class="font-semibold text-secondary-900">{{ ebayStore.account.marketplace }}</span>
                  </div>
                  <div v-if="ebayStore.account?.fulfillmentPoliciesCount !== undefined" class="flex items-center justify-between">
                    <span class="text-gray-600">Politiques de livraison</span>
                    <span class="font-semibold text-secondary-900">{{ ebayStore.account.fulfillmentPoliciesCount }}</span>
                  </div>

                  <!-- Programmes eBay -->
                  <div v-if="ebayStore.account?.programs && ebayStore.account.programs.length > 0">
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-gray-600">Programmes actifs</span>
                    </div>
                    <div class="flex flex-wrap gap-2">
                      <Badge
                        v-for="program in ebayStore.account.programs"
                        :key="program.programType"
                        :value="formatProgramName(program.programType)"
                        severity="success"
                      />
                    </div>
                  </div>

                  <!-- Token expiration -->
                  <div v-if="ebayStore.account?.accessTokenExpiresAt" class="flex items-center justify-between">
                    <span class="text-gray-600">Token expire le</span>
                    <span class="text-sm text-gray-500">{{ formatDateTime(ebayStore.account.accessTokenExpiresAt) }}</span>
                  </div>
                </div>

                <Divider />

                <div class="flex gap-3">
                  <Button
                    v-if="ebayStore.account?.storeUrl"
                    label="Voir ma boutique"
                    icon="pi pi-external-link"
                    class="bg-blue-500 hover:bg-blue-600 text-white border-0 flex-1"
                    @click="openStore"
                  />
                  <Button
                    label="Gérer sur eBay"
                    icon="pi pi-cog"
                    class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0 flex-1"
                    @click="openEbaySettings"
                  />
                </div>
              </template>
            </Card>

            <!-- Métriques avancées -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <h3 class="text-lg font-bold text-secondary-900 mb-4">Métriques de performance</h3>

                <div class="space-y-4">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-sm text-gray-600">Taux de conversion</span>
                      <span class="text-sm font-semibold text-secondary-900">{{ ebayStore.stats.conversionRate }}%</span>
                    </div>
                    <ProgressBar :value="ebayStore.stats.conversionRate * 10" :showValue="false" class="h-2" />
                  </div>

                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-sm text-gray-600">Impressions</span>
                      <span class="text-sm font-semibold text-secondary-900">{{ formatNumber(ebayStore.stats.impressions) }}</span>
                    </div>
                    <ProgressBar :value="70" :showValue="false" class="h-2" />
                  </div>

                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-sm text-gray-600">Watchers actifs</span>
                      <span class="text-sm font-semibold text-secondary-900">{{ ebayStore.stats.totalWatchers }}</span>
                    </div>
                    <ProgressBar :value="45" :showValue="false" class="h-2" />
                  </div>

                  <Divider />

                  <div class="grid grid-cols-2 gap-4">
                    <div class="text-center p-3 rounded-xl bg-gray-50">
                      <p class="text-2xl font-bold text-secondary-900">{{ formatCurrency(ebayStore.stats.averagePrice) }}</p>
                      <p class="text-xs text-gray-600">Prix moyen</p>
                    </div>
                    <div class="text-center p-3 rounded-xl bg-gray-50">
                      <p class="text-2xl font-bold text-secondary-900">{{ Math.round(ebayStore.stats.totalViews / ebayStore.stats.activeLis) }}</p>
                      <p class="text-xs text-gray-600">Vues / annonce</p>
                    </div>
                  </div>
                </div>
              </template>
            </Card>
          </div>
          </TabPanel>

          <!-- Onglet: Publications -->
          <TabPanel value="1">
          <DataTable
            :value="publications"
            :paginator="true"
            :rows="10"
            :loading="loading"
            class="modern-table"
            stripedRows
          >
            <template #empty>
              <EmptyState
                animation-type="empty-box"
                title="Aucune publication"
                description="Publiez votre premier produit sur eBay"
                action-label="Publier un produit"
                @action="$router.push('/dashboard/products')"
              />
            </template>

            <Column field="product.title" header="Produit" sortable>
              <template #body="{ data }">
                <div class="flex items-center gap-3">
                  <img
                    v-if="data.product?.image_url"
                    :src="data.product.image_url"
                    :alt="data.product.title"
                    class="w-12 h-12 rounded-lg object-cover"
                  />
                  <div class="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center" v-else>
                    <i class="pi pi-image text-gray-400"></i>
                  </div>
                  <div>
                    <p class="font-semibold text-secondary-900">{{ data.product?.title }}</p>
                    <p class="text-xs text-gray-500">ID: {{ data.product?.id }}</p>
                  </div>
                </div>
              </template>
            </Column>

            <Column field="price" header="Prix" sortable>
              <template #body="{ data }">
                <span class="font-bold text-secondary-900">{{ formatCurrency(data.price) }}</span>
              </template>
            </Column>

            <Column field="views" header="Vues" sortable>
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <i class="pi pi-eye text-gray-400 text-sm"></i>
                  <span>{{ data.views || 0 }}</span>
                </div>
              </template>
            </Column>

            <Column field="status" header="Statut" sortable>
              <template #body="{ data }">
                <Badge
                  :value="getStatusLabel(data.status)"
                  :severity="getStatusSeverity(data.status)"
                />
              </template>
            </Column>

            <Column header="Actions">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button
                    icon="pi pi-external-link"
                    class="bg-gray-100 hover:bg-gray-200 text-secondary-900 border-0"
                    size="small"
                    rounded
                    text
                    v-tooltip.top="'Voir sur eBay'"
                    @click="openPublication(data)"
                  />
                  <Button
                    icon="pi pi-euro"
                    class="bg-primary-100 hover:bg-primary-200 text-primary-700 border-0"
                    size="small"
                    rounded
                    text
                    v-tooltip.top="'Modifier le prix'"
                    @click="editPrice(data)"
                  />
                  <Button
                    icon="pi pi-trash"
                    class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                    size="small"
                    rounded
                    text
                    v-tooltip.top="'Supprimer'"
                    @click="confirmDelete(data)"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
          </TabPanel>

          <!-- Onglet: Politiques -->
          <TabPanel value="2">
          <div class="space-y-6">
            <!-- Politiques d'expédition -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                      <i class="pi pi-truck text-blue-600"></i>
                    </div>
                    <div>
                      <h3 class="text-lg font-bold text-secondary-900">Politiques d'expédition</h3>
                      <p class="text-sm text-gray-600">{{ ebayStore.shippingPolicies.length }} politique(s) configurée(s)</p>
                    </div>
                  </div>
                  <Button
                    icon="pi pi-plus"
                    label="Ajouter"
                    class="bg-blue-500 hover:bg-blue-600 text-white border-0"
                    size="small"
                    @click="openPolicyModal('shipping')"
                  />
                </div>

                <DataTable :value="ebayStore.shippingPolicies" class="modern-table" :loading="ebayStore.isLoadingPolicies">
                  <template #empty>
                    <div class="text-center py-4 text-gray-500">Aucune politique d'expédition</div>
                  </template>
                  <Column field="name" header="Nom">
                    <template #body="{ data }">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold">{{ data.name }}</span>
                        <Badge v-if="data.isDefault" value="Par défaut" severity="success" />
                      </div>
                    </template>
                  </Column>
                  <Column field="type" header="Type">
                    <template #body="{ data }">
                      <Badge
                        :value="getShippingTypeLabel(data.type)"
                        :severity="data.type === 'free_shipping' ? 'success' : 'info'"
                      />
                    </template>
                  </Column>
                  <Column field="domesticShipping.cost" header="Coût">
                    <template #body="{ data }">
                      {{ data.type === 'free_shipping' ? 'Gratuit' : formatCurrency(data.domesticShipping.cost) }}
                    </template>
                  </Column>
                  <Column header="Actions">
                    <template #body="{ data }">
                      <Button
                        icon="pi pi-trash"
                        class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                        size="small"
                        rounded
                        text
                        :disabled="data.isDefault"
                        @click="deletePolicy('shipping', data.id)"
                      />
                    </template>
                  </Column>
                </DataTable>
              </template>
            </Card>

            <!-- Politiques de retour -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                      <i class="pi pi-replay text-orange-600"></i>
                    </div>
                    <div>
                      <h3 class="text-lg font-bold text-secondary-900">Politiques de retour</h3>
                      <p class="text-sm text-gray-600">{{ ebayStore.returnPolicies.length }} politique(s) configurée(s)</p>
                    </div>
                  </div>
                  <Button
                    icon="pi pi-plus"
                    label="Ajouter"
                    class="bg-orange-500 hover:bg-orange-600 text-white border-0"
                    size="small"
                    @click="openPolicyModal('return')"
                  />
                </div>

                <DataTable :value="ebayStore.returnPolicies" class="modern-table" :loading="ebayStore.isLoadingPolicies">
                  <template #empty>
                    <div class="text-center py-4 text-gray-500">Aucune politique de retour</div>
                  </template>
                  <Column field="name" header="Nom">
                    <template #body="{ data }">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold">{{ data.name }}</span>
                        <Badge v-if="data.isDefault" value="Par défaut" severity="success" />
                      </div>
                    </template>
                  </Column>
                  <Column field="returnsAccepted" header="Retours">
                    <template #body="{ data }">
                      <Badge
                        :value="data.returnsAccepted ? 'Acceptés' : 'Refusés'"
                        :severity="data.returnsAccepted ? 'success' : 'danger'"
                      />
                    </template>
                  </Column>
                  <Column field="returnPeriod" header="Délai">
                    <template #body="{ data }">
                      {{ data.returnsAccepted ? `${data.returnPeriod} jours` : '-' }}
                    </template>
                  </Column>
                  <Column field="shippingCostPaidBy" header="Frais retour">
                    <template #body="{ data }">
                      {{ data.shippingCostPaidBy === 'seller' ? 'Vendeur' : 'Acheteur' }}
                    </template>
                  </Column>
                  <Column header="Actions">
                    <template #body="{ data }">
                      <Button
                        icon="pi pi-trash"
                        class="bg-red-100 hover:bg-red-200 text-red-700 border-0"
                        size="small"
                        rounded
                        text
                        :disabled="data.isDefault"
                        @click="deletePolicy('return', data.id)"
                      />
                    </template>
                  </Column>
                </DataTable>
              </template>
            </Card>

            <!-- Politiques de paiement -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                      <i class="pi pi-credit-card text-green-600"></i>
                    </div>
                    <div>
                      <h3 class="text-lg font-bold text-secondary-900">Politiques de paiement</h3>
                      <p class="text-sm text-gray-600">{{ ebayStore.paymentPolicies.length }} politique(s) configurée(s)</p>
                    </div>
                  </div>
                </div>

                <DataTable :value="ebayStore.paymentPolicies" class="modern-table" :loading="ebayStore.isLoadingPolicies">
                  <template #empty>
                    <div class="text-center py-4 text-gray-500">Aucune politique de paiement</div>
                  </template>
                  <Column field="name" header="Nom">
                    <template #body="{ data }">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold">{{ data.name }}</span>
                        <Badge v-if="data.isDefault" value="Par défaut" severity="success" />
                      </div>
                    </template>
                  </Column>
                  <Column field="paymentMethods" header="Méthodes">
                    <template #body="{ data }">
                      <div class="flex gap-1">
                        <Badge
                          v-for="method in data.paymentMethods"
                          :key="method"
                          :value="getPaymentMethodLabel(method)"
                          severity="secondary"
                        />
                      </div>
                    </template>
                  </Column>
                  <Column field="immediatePay" header="Paiement immédiat">
                    <template #body="{ data }">
                      <i :class="data.immediatePay ? 'pi pi-check text-green-600' : 'pi pi-times text-gray-400'"></i>
                    </template>
                  </Column>
                </DataTable>
              </template>
            </Card>
          </div>
          </TabPanel>

          <!-- Onglet: Catégories -->
          <TabPanel value="3">
          <Card class="shadow-sm modern-rounded border border-gray-100">
            <template #content>
              <div class="flex items-center justify-between mb-6">
                <div>
                  <h3 class="text-lg font-bold text-secondary-900">Catégories eBay</h3>
                  <p class="text-sm text-gray-600">Sélectionnez les catégories pour vos produits</p>
                </div>
                <Button
                  icon="pi pi-refresh"
                  label="Actualiser"
                  class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
                  size="small"
                  :loading="ebayStore.isLoadingCategories"
                  @click="loadCategories"
                />
              </div>

              <Tree
                :value="ebayStore.categories"
                v-model:selectionKeys="selectedCategoryKeys"
                selectionMode="checkbox"
                :loading="ebayStore.isLoadingCategories"
                class="w-full"
              >
                <template #default="slotProps">
                  <div class="flex items-center gap-2">
                    <span>{{ slotProps.node.name }}</span>
                    <Badge v-if="slotProps.node.leafCategory" value="Feuille" severity="secondary" />
                  </div>
                </template>
              </Tree>

              <Divider />

              <div class="flex justify-end">
                <Button
                  label="Sauvegarder la sélection"
                  icon="pi pi-save"
                  class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
                  @click="saveCategories"
                />
              </div>
            </template>
          </Card>
          </TabPanel>

          <!-- Onglet: Paramètres -->
          <TabPanel value="4">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Paramètres de synchronisation -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <h3 class="text-lg font-bold text-secondary-900 mb-4">Synchronisation</h3>

                <div class="space-y-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900 mb-1">Synchronisation automatique</p>
                      <p class="text-sm text-gray-600">Synchroniser les données automatiquement</p>
                    </div>
                    <ToggleSwitch v-model="syncSettings.autoSync" />
                  </div>

                  <div v-if="syncSettings.autoSync">
                    <label class="block font-semibold text-secondary-900 mb-2">Intervalle de synchronisation</label>
                    <Select
                      v-model="syncSettings.syncInterval"
                      :options="syncIntervals"
                      optionLabel="label"
                      optionValue="value"
                      class="w-full"
                    />
                  </div>

                  <Divider />

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900 mb-1">Synchroniser le stock</p>
                      <p class="text-sm text-gray-600">Mettre à jour le stock automatiquement</p>
                    </div>
                    <ToggleSwitch v-model="syncSettings.syncStock" />
                  </div>

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900 mb-1">Synchroniser les prix</p>
                      <p class="text-sm text-gray-600">Mettre à jour les prix automatiquement</p>
                    </div>
                    <ToggleSwitch v-model="syncSettings.syncPrices" />
                  </div>

                  <div class="flex items-center justify-between">
                    <div>
                      <p class="font-semibold text-secondary-900 mb-1">Synchroniser les descriptions</p>
                      <p class="text-sm text-gray-600">Mettre à jour les descriptions automatiquement</p>
                    </div>
                    <ToggleSwitch v-model="syncSettings.syncDescriptions" />
                  </div>
                </div>
              </template>
            </Card>

            <!-- Paramètres de listing -->
            <Card class="shadow-sm modern-rounded border border-gray-100">
              <template #content>
                <h3 class="text-lg font-bold text-secondary-900 mb-4">Paramètres par défaut</h3>

                <div class="space-y-6">
                  <div>
                    <label class="block font-semibold text-secondary-900 mb-2">Type de listing par défaut</label>
                    <Select
                      v-model="listingSettings.defaultListingType"
                      :options="listingTypes"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Sélectionnez un type"
                      class="w-full"
                    />
                  </div>

                  <div>
                    <label class="block font-semibold text-secondary-900 mb-2">Durée de listing par défaut</label>
                    <Select
                      v-model="listingSettings.defaultDuration"
                      :options="durations"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Sélectionnez une durée"
                      class="w-full"
                    />
                  </div>

                  <div>
                    <label class="block font-semibold text-secondary-900 mb-2">Politique d'expédition par défaut</label>
                    <Select
                      v-model="listingSettings.defaultShippingPolicy"
                      :options="ebayStore.shippingPolicies"
                      optionLabel="name"
                      optionValue="id"
                      placeholder="Sélectionnez une politique"
                      class="w-full"
                    />
                  </div>

                  <div>
                    <label class="block font-semibold text-secondary-900 mb-2">Politique de retour par défaut</label>
                    <Select
                      v-model="listingSettings.defaultReturnPolicy"
                      :options="ebayStore.returnPolicies"
                      optionLabel="name"
                      optionValue="id"
                      placeholder="Sélectionnez une politique"
                      class="w-full"
                    />
                  </div>
                </div>
              </template>
            </Card>
          </div>

          <div class="flex justify-end mt-6">
            <Button
              label="Sauvegarder les paramètres"
              icon="pi pi-save"
              class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
              @click="saveSettings"
            />
          </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </template>

    <!-- Modal: Modifier le prix -->
    <Dialog
      v-model:visible="priceModalVisible"
      modal
      header="Modifier le prix"
      :style="{ width: '400px' }"
    >
      <div v-if="selectedPublication" class="space-y-4">
        <div>
          <p class="font-semibold text-secondary-900 mb-2">{{ selectedPublication.product?.title }}</p>
          <p class="text-sm text-gray-600 mb-4">Prix actuel: {{ formatCurrency(selectedPublication.price) }}</p>
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nouveau prix</label>
          <InputNumber
            v-model="newPrice"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
            :maxFractionDigits="2"
          />
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          icon="pi pi-times"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="priceModalVisible = false"
        />
        <Button
          label="Sauvegarder"
          icon="pi pi-check"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click="updatePrice"
        />
      </template>
    </Dialog>

    <!-- Modal: Nouvelle politique d'expédition -->
    <Dialog
      v-model:visible="shippingPolicyModal"
      modal
      header="Nouvelle politique d'expédition"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
          <InputText v-model="newShippingPolicy.name" class="w-full" placeholder="Ex: Livraison Standard" />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Description</label>
          <Textarea v-model="newShippingPolicy.description" class="w-full" rows="2" placeholder="Description optionnelle" />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Type d'expédition</label>
          <Select
            v-model="newShippingPolicy.type"
            :options="shippingTypes"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>

        <div v-if="newShippingPolicy.type !== 'free_shipping'">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Coût d'expédition (EUR)</label>
          <InputNumber
            v-model="newShippingPolicy.cost"
            mode="currency"
            currency="EUR"
            locale="fr-FR"
            class="w-full"
            :min="0"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Délai de traitement (jours)</label>
          <InputNumber v-model="newShippingPolicy.handlingTime" class="w-full" :min="0" :max="30" />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newShippingPolicy.isDefault" :binary="true" />
          <label class="text-sm text-secondary-900">Définir comme politique par défaut</label>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="shippingPolicyModal = false"
        />
        <Button
          label="Créer"
          icon="pi pi-check"
          class="bg-blue-500 hover:bg-blue-600 text-white border-0 font-semibold"
          @click="createShippingPolicy"
        />
      </template>
    </Dialog>

    <!-- Modal: Nouvelle politique de retour -->
    <Dialog
      v-model:visible="returnPolicyModal"
      modal
      header="Nouvelle politique de retour"
      :style="{ width: '500px' }"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Nom de la politique *</label>
          <InputText v-model="newReturnPolicy.name" class="w-full" placeholder="Ex: Retours 30 jours" />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newReturnPolicy.returnsAccepted" :binary="true" />
          <label class="text-sm text-secondary-900">Accepter les retours</label>
        </div>

        <div v-if="newReturnPolicy.returnsAccepted">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Période de retour (jours)</label>
          <InputNumber v-model="newReturnPolicy.returnPeriod" class="w-full" :min="1" :max="60" />
        </div>

        <div v-if="newReturnPolicy.returnsAccepted">
          <label class="block text-sm font-semibold text-secondary-900 mb-2">Frais de retour payés par</label>
          <Select
            v-model="newReturnPolicy.shippingCostPaidBy"
            :options="[{ label: 'Acheteur', value: 'buyer' }, { label: 'Vendeur', value: 'seller' }]"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>

        <div class="flex items-center gap-2">
          <Checkbox v-model="newReturnPolicy.isDefault" :binary="true" />
          <label class="text-sm text-secondary-900">Définir comme politique par défaut</label>
        </div>
      </div>

      <template #footer>
        <Button
          label="Annuler"
          class="bg-gray-200 hover:bg-gray-300 text-secondary-900 border-0"
          @click="returnPolicyModal = false"
        />
        <Button
          label="Créer"
          icon="pi pi-check"
          class="bg-orange-500 hover:bg-orange-600 text-white border-0 font-semibold"
          @click="createReturnPolicy"
        />
      </template>
    </Dialog>

    <!-- Confirm Dialog -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'

definePageMeta({
  layout: 'dashboard'
})

// SSR-safe initialization: Only call PrimeVue hooks on client-side
const confirm = import.meta.client ? useConfirm() : null
const ebayStore = useEbayStore()
const publicationsStore = usePublicationsStore()
const { showSuccess, showError, showInfo, showWarn } = useAppToast()

// State
const activeTab = ref('0')
const loading = ref(false)
const priceModalVisible = ref(false)
const shippingPolicyModal = ref(false)
const returnPolicyModal = ref(false)
const selectedPublication = ref<any>(null)
const newPrice = ref(0)
const selectedCategoryKeys = ref<Record<string, boolean>>({})

// Sync settings (local copy for editing)
const syncSettings = reactive({
  autoSync: true,
  syncInterval: 30,
  syncStock: true,
  syncPrices: true,
  syncDescriptions: false
})

// Listing settings
const listingSettings = reactive({
  defaultListingType: 'FixedPrice',
  defaultDuration: 'GTC',
  defaultShippingPolicy: '',
  defaultReturnPolicy: ''
})

// New policy forms
const newShippingPolicy = reactive({
  name: '',
  description: '',
  type: 'flat_rate' as 'flat_rate' | 'calculated' | 'free_shipping',
  cost: 5.99,
  handlingTime: 1,
  isDefault: false
})

const newReturnPolicy = reactive({
  name: '',
  returnsAccepted: true,
  returnPeriod: 30,
  shippingCostPaidBy: 'buyer' as 'buyer' | 'seller',
  isDefault: false
})

// Options
const syncIntervals = [
  { label: 'Toutes les 15 minutes', value: 15 },
  { label: 'Toutes les 30 minutes', value: 30 },
  { label: 'Toutes les heures', value: 60 },
  { label: 'Toutes les 2 heures', value: 120 },
  { label: 'Toutes les 6 heures', value: 360 }
]

const listingTypes = [
  { label: 'Prix fixe', value: 'FixedPrice' },
  { label: 'Enchère', value: 'Auction' },
  { label: 'Meilleure offre', value: 'BestOffer' }
]

const durations = [
  { label: '3 jours', value: '3' },
  { label: '5 jours', value: '5' },
  { label: '7 jours', value: '7' },
  { label: '10 jours', value: '10' },
  { label: '30 jours', value: '30' },
  { label: 'Bonne affaire jusqu\'à annulation', value: 'GTC' }
]

const shippingTypes = [
  { label: 'Forfait', value: 'flat_rate' },
  { label: 'Calculé', value: 'calculated' },
  { label: 'Gratuit', value: 'free_shipping' }
]

// Computed
const publications = computed(() => {
  return publicationsStore.publications
    .filter((p: any) => p.platform === 'ebay')
    .map((p: any) => ({
      ...p,
      product: { id: p.product_id, title: p.product_title },
      views: Math.floor(Math.random() * 150)
    }))
})

// Methods
const handleConnect = async () => {
  try {
    // Utiliser l'OAuth réel
    await ebayStore.initiateOAuth()

    showSuccess(
      'Connexion réussie',
      'Votre compte eBay a été connecté avec succès',
      3000
    )
  } catch (error: any) {
    showError(
      'Erreur de connexion',
      error.message || 'Impossible de connecter à eBay',
      5000
    )
  }
}

const handleDisconnect = () => {
  confirm?.require({
    message: 'Voulez-vous vraiment déconnecter votre compte eBay ? Vos publications resteront actives sur eBay.',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Oui, déconnecter',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await ebayStore.disconnect()

        showInfo(
          'Déconnecté',
          'Votre compte eBay a été déconnecté',
          3000
        )
      } catch (error) {
        showError(
          'Erreur',
          'Impossible de déconnecter le compte',
          5000
        )
      }
    }
  })
}

const handleSync = async () => {
  try {
    await ebayStore.fetchStats()
    await ebayStore.fetchPolicies()

    showSuccess(
      'Synchronisation terminée',
      'Vos données eBay sont à jour',
      3000
    )
  } catch (error) {
    showError(
      'Erreur',
      'Échec de la synchronisation',
      5000
    )
  }
}

const openStore = () => {
  if (ebayStore.account?.storeUrl) {
    window.open(ebayStore.account.storeUrl, '_blank')
  }
}

const openEbaySettings = () => {
  window.open('https://www.ebay.fr/sh/ovw', '_blank')
}

const openPublication = (publication: any) => {
  const url = `https://www.ebay.fr/itm/${publication.id}`
  window.open(url, '_blank')
}

const editPrice = (publication: any) => {
  selectedPublication.value = publication
  newPrice.value = publication.price
  priceModalVisible.value = true
}

const updatePrice = async () => {
  if (!selectedPublication.value) return

  try {
    selectedPublication.value.price = newPrice.value

    showSuccess(
      'Prix modifié',
      'Le prix a été mis à jour sur eBay',
      3000
    )

    priceModalVisible.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de modifier le prix',
      5000
    )
  }
}

const confirmDelete = (publication: any) => {
  confirm?.require({
    message: `Voulez-vous vraiment supprimer "${publication.product?.title}" de eBay ?`,
    header: 'Confirmation de suppression',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      showSuccess(
        'Publication supprimée',
        'La publication a été retirée de eBay',
        3000
      )
    }
  })
}

const openPolicyModal = (type: 'shipping' | 'return') => {
  if (type === 'shipping') {
    Object.assign(newShippingPolicy, {
      name: '',
      description: '',
      type: 'flat_rate',
      cost: 5.99,
      handlingTime: 1,
      isDefault: false
    })
    shippingPolicyModal.value = true
  } else {
    Object.assign(newReturnPolicy, {
      name: '',
      returnsAccepted: true,
      returnPeriod: 30,
      shippingCostPaidBy: 'buyer',
      isDefault: false
    })
    returnPolicyModal.value = true
  }
}

const createShippingPolicy = async () => {
  if (!newShippingPolicy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createShippingPolicy({
      name: newShippingPolicy.name,
      description: newShippingPolicy.description,
      type: newShippingPolicy.type,
      domesticShipping: {
        service: 'FR_ColipostColissimo',
        cost: newShippingPolicy.type === 'free_shipping' ? 0 : newShippingPolicy.cost,
        handlingTime: newShippingPolicy.handlingTime
      },
      isDefault: newShippingPolicy.isDefault
    })

    showSuccess(
      'Politique créée',
      'La politique d\'expédition a été créée',
      3000
    )

    shippingPolicyModal.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de créer la politique',
      5000
    )
  }
}

const createReturnPolicy = async () => {
  if (!newReturnPolicy.name) {
    showWarn('Validation', 'Le nom est requis', 3000)
    return
  }

  try {
    await ebayStore.createReturnPolicy({
      name: newReturnPolicy.name,
      returnsAccepted: newReturnPolicy.returnsAccepted,
      returnPeriod: newReturnPolicy.returnsAccepted ? newReturnPolicy.returnPeriod : 0,
      refundMethod: 'money_back',
      shippingCostPaidBy: newReturnPolicy.shippingCostPaidBy,
      isDefault: newReturnPolicy.isDefault
    })

    showSuccess(
      'Politique créée',
      'La politique de retour a été créée',
      3000
    )

    returnPolicyModal.value = false
  } catch (error) {
    showError(
      'Erreur',
      'Impossible de créer la politique',
      5000
    )
  }
}

const deletePolicy = async (type: 'shipping' | 'return' | 'payment', policyId: string) => {
  confirm?.require({
    message: 'Voulez-vous vraiment supprimer cette politique ?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Supprimer',
    rejectLabel: 'Annuler',
    accept: async () => {
      try {
        await ebayStore.deletePolicy(type, policyId)
        showSuccess(
          'Politique supprimée',
          'La politique a été supprimée',
          3000
        )
      } catch (error) {
        showError(
          'Erreur',
          'Impossible de supprimer la politique',
          5000
        )
      }
    }
  })
}

const loadCategories = async () => {
  // TODO: Implémenter fetchCategories() dans le store quand l'API sera prête
  showInfo('Information', 'La synchronisation des catégories sera disponible prochainement', 3000)
}

const saveCategories = () => {
  showSuccess(
    'Catégories sauvegardées',
    'Vos catégories préférées ont été enregistrées',
    3000
  )
}

const saveSettings = async () => {
  await ebayStore.saveSyncSettings(syncSettings)

  showSuccess(
    'Paramètres sauvegardés',
    'Vos préférences ont été enregistrées',
    3000
  )
}

// Helper functions
const getSellerLevelSeverity = () => {
  const level = ebayStore.account?.sellerLevel
  if (level === 'top_rated') return 'success'
  if (level === 'above_standard') return 'info'
  if (level === 'standard') return 'warning'
  return 'danger'
}

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    active: 'Actif',
    published: 'Publié',
    sold: 'Vendu',
    paused: 'En pause',
    expired: 'Expiré',
    draft: 'Brouillon'
  }
  return labels[status] || status
}

const getStatusSeverity = (status: string): string => {
  const severities: Record<string, string> = {
    active: 'success',
    published: 'success',
    sold: 'info',
    paused: 'warning',
    expired: 'danger',
    draft: 'secondary'
  }
  return severities[status] || 'secondary'
}

const getShippingTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    flat_rate: 'Forfait',
    calculated: 'Calculé',
    free_shipping: 'Gratuit'
  }
  return labels[type] || type
}

const getPaymentMethodLabel = (method: string): string => {
  const labels: Record<string, string> = {
    paypal: 'PayPal',
    credit_card: 'Carte',
    bank_transfer: 'Virement'
  }
  return labels[method] || method
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(value || 0)
}

const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('fr-FR').format(value || 0)
}

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

const formatRelativeTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'À l\'instant'
  if (minutes < 60) return `Il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Il y a ${hours}h`
  const days = Math.floor(hours / 24)
  return `Il y a ${days}j`
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatProgramName = (programType: string): string => {
  const names: Record<string, string> = {
    'SELLING_POLICY_MANAGEMENT': 'Gestion Politiques',
    'PROMOTED_LISTINGS_STANDARD': 'Annonces sponsorisées',
    'OFFSITE_ADS': 'Publicités hors site',
    'OUT_OF_STOCK_CONTROL': 'Contrôle stock'
  }
  return names[programType] || programType.replace(/_/g, ' ')
}

// Initialize on mount
onMounted(async () => {
  // Vérifier le statut de connexion au chargement
  try {
    await ebayStore.checkConnectionStatus()
  } catch (error) {
    console.error('Erreur vérification statut eBay:', error)
  }

  if (ebayStore.isConnected) {
    loading.value = true
    try {
      await Promise.all([
        publicationsStore.fetchPublications(),
        ebayStore.fetchPolicies(),
        ebayStore.fetchStats()
        // Note: Account info est maintenant chargé via checkConnectionStatus()
      ])

      // Sync local settings
      Object.assign(syncSettings, ebayStore.syncSettings)

      // Set default policies
      if (ebayStore.defaultShippingPolicy) {
        listingSettings.defaultShippingPolicy = ebayStore.defaultShippingPolicy.id
      }
      if (ebayStore.defaultReturnPolicy) {
        listingSettings.defaultReturnPolicy = ebayStore.defaultReturnPolicy.id
      }
    } catch (error) {
      console.error('Erreur chargement données:', error)
    } finally {
      loading.value = false
    }
  }
})
</script>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover::before {
  opacity: 1;
}

.modern-table {
  border-radius: 16px;
  overflow: hidden;
}

.ebay-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border: none;
}

.ebay-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #6b7280;
  transition: all 0.2s ease;
}

.ebay-tabs :deep(.p-tabview-nav-link:not(.p-disabled):focus) {
  box-shadow: none;
}

.ebay-tabs :deep(.p-highlight .p-tabview-nav-link) {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.ebay-tabs :deep(.p-tabview-panels) {
  background: transparent;
  padding: 1.5rem 0;
}
</style>
