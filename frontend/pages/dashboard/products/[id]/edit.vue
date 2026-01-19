<template>
  <ProductsProductEditorView
    mode="edit"
    :product-id="productId"
    @success="handleSuccess"
    @cancel="router.push('/dashboard/products')"
  />
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const router = useRouter()

const productId = parseInt(route.params.id as string)

const handleSuccess = () => {
  router.push('/dashboard/products')
}
</script>
