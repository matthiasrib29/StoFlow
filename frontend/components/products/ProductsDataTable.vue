<template>
  <DataTable
    v-model:selection="selectedProducts"
    :value="products"
    data-key="id"
    :lazy="true"
    :paginator="true"
    :rows="rowsPerPage"
    :total-records="totalRecords"
    :first="(currentPage - 1) * rowsPerPage"
    :rows-per-page-options="[10, 20, 50, 100]"
    paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
    current-page-report-template="{first}-{last} sur {totalRecords} produits"
    :loading="loading"
    class="products-table"
    @page="$emit('page', $event)"
  >
    <template #empty>
      <div class="text-center py-16">
        <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
          <i class="pi pi-box text-4xl text-gray-300"/>
        </div>
        <p class="text-secondary-900 font-semibold text-lg mb-1">Aucun produit</p>
        <p class="text-gray-400 text-sm mb-6">Commencez par créer votre premier produit</p>
        <Button
          label="Créer un produit"
          icon="pi pi-plus"
          class="bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0 font-semibold"
          @click="$emit('create')"
        />
      </div>
    </template>

    <Column selection-mode="multiple" header-style="width: 3rem" />

    <Column field="image_url" header="" style="width: 70px">
      <template #body="slotProps">
        <img
          :src="getProductImageUrl(slotProps.data)"
          :alt="slotProps.data.title"
          class="w-12 h-12 object-cover rounded-lg"
        >
      </template>
    </Column>

    <Column field="title" header="Produit" sortable style="min-width: 220px">
      <template #body="slotProps">
        <div>
          <p class="font-semibold text-secondary-900">{{ slotProps.data.title }}</p>
          <p class="text-xs text-gray-400">{{ slotProps.data.id }}</p>
        </div>
      </template>
    </Column>

    <Column field="brand" header="Marque" sortable>
      <template #body="slotProps">
        <span class="text-secondary-800">{{ slotProps.data.brand }}</span>
      </template>
    </Column>

    <Column field="category" header="Catégorie" sortable>
      <template #body="slotProps">
        <span class="text-sm text-gray-600">{{ slotProps.data.category }}</span>
      </template>
    </Column>

    <Column field="price" header="Prix" sortable style="width: 100px">
      <template #body="slotProps">
        <span class="font-semibold text-secondary-900">{{ formatPrice(slotProps.data.price) }}</span>
      </template>
    </Column>

    <Column field="status" header="Statut" sortable style="width: 100px">
      <template #body="slotProps">
        <span
          class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium"
          :class="getStatusClass(slotProps.data.status)"
        >
          <span class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(slotProps.data.status)" />
          {{ getStatusLabel(slotProps.data.status) }}
        </span>
      </template>
    </Column>

    <Column header="Plateformes" style="width: 100px">
      <template #body="slotProps">
        <div class="flex items-center gap-2">
          <img
            v-if="slotProps.data.vinted_id"
            src="/images/platforms/vinted-logo.png"
            alt="Vinted"
            class="w-10 h-10 object-contain"
            title="Lié à Vinted"
          >
          <img
            v-if="slotProps.data.ebay_id"
            src="/images/platforms/ebay-logo.png"
            alt="eBay"
            class="w-10 h-10 object-contain"
            title="Lié à eBay"
          >
          <span
            v-if="!slotProps.data.vinted_id && !slotProps.data.ebay_id"
            class="text-xs text-gray-400"
          >
            —
          </span>
        </div>
      </template>
    </Column>

    <Column header="" style="width: 90px">
      <template #body="slotProps">
        <div class="flex gap-1 justify-end">
          <button
            class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
            @click="$emit('edit', slotProps.data)"
          >
            <i class="pi pi-pencil text-sm"/>
          </button>
          <button
            class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            title="Archiver"
            @click="$emit('delete', slotProps.data)"
          >
            <i class="pi pi-inbox text-sm"/>
          </button>
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { Product } from '~/stores/products'
import { getProductImageUrl } from '~/stores/products'
import { formatPrice } from '~/utils/formatters'

// Status helpers (values match API response: lowercase)
const statusConfig: Record<string, { label: string; class: string; dot: string }> = {
  draft: { label: 'Brouillon', class: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400' },
  published: { label: 'Publié', class: 'bg-success-50 text-success-700', dot: 'bg-success-500' },
  sold: { label: 'Vendu', class: 'bg-primary-100 text-primary-700', dot: 'bg-primary-500' },
  archived: { label: 'Archivé', class: 'bg-gray-100 text-gray-500', dot: 'bg-gray-300' }
}

const getStatusLabel = (status: string) => statusConfig[status]?.label || status
const getStatusClass = (status: string) => statusConfig[status]?.class || 'bg-gray-100 text-gray-600'
const getStatusDotClass = (status: string) => statusConfig[status]?.dot || 'bg-gray-400'

defineProps<{
  products: Product[]
  totalRecords: number
  currentPage: number
  rowsPerPage: number
  loading: boolean
}>()

const selectedProducts = defineModel<Product[]>('selection', { default: [] })

defineEmits<{
  page: [event: { page: number; rows: number }]
  edit: [product: Product]
  delete: [product: Product]
  create: []
}>()
</script>

<style scoped>
:deep(.products-table) {
  .p-datatable-header {
    display: none;
  }

  .p-datatable-thead > tr > th {
    background: transparent;
    border: none;
    border-bottom: 1px solid #f3f4f6;
    padding: 0.75rem 1rem;
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af;
  }

  .p-datatable-tbody > tr {
    transition: background-color 0.1s ease;
  }

  .p-datatable-tbody > tr > td {
    border: none;
    border-bottom: 1px solid #f9fafb;
    padding: 0.75rem 1rem;
    vertical-align: middle;
  }

  .p-datatable-tbody > tr:hover {
    background: #fffbeb !important;
  }

  .p-datatable-tbody > tr:last-child > td {
    border-bottom: none;
  }

  /* Paginator */
  .p-paginator {
    background: #fafafa;
    border: none;
    border-top: 1px solid #f3f4f6;
    padding: 0.75rem 1rem;
    justify-content: flex-end;
    gap: 0.5rem;
  }

  .p-paginator .p-paginator-pages .p-paginator-page {
    min-width: 2rem;
    height: 2rem;
    border-radius: 0.375rem;
    margin: 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .p-paginator .p-paginator-pages .p-paginator-page:hover {
    background: #f3f4f6;
  }

  .p-paginator .p-paginator-pages .p-paginator-page.p-highlight {
    background: #facc15;
    color: #1f2937;
    border-color: #facc15;
    font-weight: 600;
  }

  .p-paginator .p-dropdown {
    height: 2rem;
    border-radius: 0.375rem;
    border-color: #e5e7eb;
  }

  .p-paginator-first,
  .p-paginator-prev,
  .p-paginator-next,
  .p-paginator-last {
    min-width: 2rem;
    height: 2rem;
    border-radius: 0.375rem;
    color: #6b7280;
  }

  .p-paginator-first:hover,
  .p-paginator-prev:hover,
  .p-paginator-next:hover,
  .p-paginator-last:hover {
    background: #f3f4f6;
  }

  .p-paginator-current {
    font-size: 0.875rem;
    color: #6b7280;
  }

  /* Checkbox styling */
  .p-checkbox .p-checkbox-box {
    width: 1.125rem;
    height: 1.125rem;
    border-radius: 0.25rem;
    border-color: #d1d5db;
  }

  .p-checkbox .p-checkbox-box.p-highlight {
    background: #facc15;
    border-color: #facc15;
  }

  .p-checkbox .p-checkbox-box .p-checkbox-icon {
    color: #1f2937;
  }
}
</style>
