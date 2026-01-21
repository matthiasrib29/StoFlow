<template>
  <div>
    <!-- Redirecting to beta page... -->
  </div>
</template>

<script setup lang="ts">
/**
 * Beta Phase Redirect
 *
 * During beta, all traffic to the homepage is redirected to /beta
 * Remove this file and restore the original landing page when launching the full product
 */
definePageMeta({
  layout: false
})

// Immediate redirect to beta signup page
await navigateTo('/beta', { redirectCode: 302 })
</script>
