<template>
  <div>
    <button
      class="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
      :class="{ 'bg-primary-50 text-secondary-900 font-semibold': isActive }"
      @click="$emit('toggle')"
    >
      <div class="flex items-center gap-3">
        <img :src="logo" :alt="label" class="w-5 h-5 object-contain">
        <span>{{ label }}</span>
      </div>
      <i :class="['pi pi-chevron-down text-sm transition-transform duration-300', isOpen ? 'rotate-180' : 'rotate-0']"/>
    </button>

    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-96"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 max-h-96"
      leave-to-class="opacity-0 max-h-0"
    >
      <div v-if="isOpen" class="ml-3 mt-1 space-y-1 overflow-hidden border-l-2 border-gray-100 pl-3">
        <NuxtLink
          :to="`/dashboard/platforms/${platform}/products`"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-box text-sm"/>
          <span>Produits {{ label }}</span>
        </NuxtLink>
        <NuxtLink
          :to="`/dashboard/platforms/${platform}/${platform === 'vinted' ? 'sales' : 'orders'}`"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-shopping-bag text-sm"/>
          <span>Commandes</span>
        </NuxtLink>
        <NuxtLink
          :to="`/dashboard/platforms/${platform}/statistics`"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-chart-bar text-sm"/>
          <span>Statistiques</span>
        </NuxtLink>
        <NuxtLink
          :to="`/dashboard/platforms/${platform}/settings`"
          class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
          active-class="bg-primary-50 text-secondary-900 font-semibold"
        >
          <i class="pi pi-cog text-sm"/>
          <span>Paramètres</span>
        </NuxtLink>

        <!-- eBay-specific: Post-Sale Management -->
        <template v-if="platform === 'ebay'">
          <div class="my-2 border-t border-gray-100" />
          <NuxtLink
            to="/dashboard/platforms/ebay/returns"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-replay text-sm"/>
            <span>Retours</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/platforms/ebay/cancellations"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-times-circle text-sm"/>
            <span>Annulations</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/platforms/ebay/refunds"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-euro text-sm"/>
            <span>Remboursements</span>
          </NuxtLink>
          <NuxtLink
            to="/dashboard/platforms/ebay/payment-disputes"
            class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all text-gray-500 text-sm font-medium"
            active-class="bg-primary-50 text-secondary-900 font-semibold"
          >
            <i class="pi pi-exclamation-triangle text-sm"/>
            <span>Litiges</span>
          </NuxtLink>
        </template>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  platform: 'vinted' | 'ebay' | 'etsy'
  label: string
  logo: string
  isActive?: boolean
  isOpen: boolean
}>()

defineEmits<{
  toggle: []
}>()

const route = useRoute()
</script>
