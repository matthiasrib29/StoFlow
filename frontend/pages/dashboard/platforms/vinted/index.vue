<script setup lang="ts">
/**
 * Vinted Platform Index - Redirect to products
 *
 * This page redirects to the products page since there's no landing page
 * for the Vinted platform section.
 */
definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()

// Redirect to products page
onMounted(() => {
  router.replace('/dashboard/platforms/vinted/products')
})
</script>

<template>
  <div class="flex items-center justify-center min-h-[400px]">
    <div class="text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-4"></div>
      <p class="text-gray-500">Redirection...</p>
    </div>
  </div>
</template>
