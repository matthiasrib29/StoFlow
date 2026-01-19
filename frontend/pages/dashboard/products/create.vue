<template>
  <ProductsProductEditorView
    mode="create"
    @success="handleSuccess"
    @cancel="router.push('/dashboard/products')"
  />
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const router = useRouter()

const handleSuccess = () => {
  router.push('/dashboard/products')
}
</script>
