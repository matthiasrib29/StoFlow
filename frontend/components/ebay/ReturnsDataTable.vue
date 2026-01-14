<template>
  <DataTable
    :value="returns"
    data-key="id"
    :lazy="true"
    :paginator="true"
    :rows="rowsPerPage"
    :total-records="totalRecords"
    :first="(currentPage - 1) * rowsPerPage"
    :rows-per-page-options="[10, 20, 50, 100]"
    paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
    current-page-report-template="{first}-{last} sur {totalRecords} retours"
    :loading="loading"
    class="returns-table"
    @page="$emit('page', $event)"
    @row-click="$emit('row-click', $event)"
  >
    <template #empty>
      <div class="text-center py-16">
        <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center mx-auto mb-4">
          <i class="pi pi-undo text-4xl text-gray-300" />
        </div>
        <p class="text-secondary-900 font-semibold text-lg mb-1">Aucun retour</p>
        <p class="text-gray-400 text-sm mb-6">Les retours eBay apparaîtront ici</p>
        <Button
          label="Synchroniser"
          icon="pi pi-sync"
          class="bg-platform-ebay hover:bg-platform-ebay/90 text-white border-0 font-semibold"
          @click="$emit('sync')"
        />
      </div>
    </template>

    <!-- Return ID -->
    <Column field="return_id" header="ID Retour" sortable style="width: 140px">
      <template #body="slotProps">
        <div>
          <p class="font-mono text-sm text-secondary-900">{{ slotProps.data.return_id }}</p>
          <p
            v-if="slotProps.data.is_past_deadline"
            class="text-xs text-red-500 font-medium flex items-center gap-1 mt-0.5"
          >
            <i class="pi pi-exclamation-triangle text-xs" />
            En retard
          </p>
        </div>
      </template>
    </Column>

    <!-- Order ID -->
    <Column field="order_id" header="Commande" sortable style="width: 120px">
      <template #body="slotProps">
        <span class="font-mono text-sm text-gray-600">
          {{ slotProps.data.order_id || '-' }}
        </span>
      </template>
    </Column>

    <!-- Buyer -->
    <Column field="buyer_username" header="Acheteur" sortable style="min-width: 120px">
      <template #body="slotProps">
        <span class="text-secondary-800">
          {{ slotProps.data.buyer_username || '-' }}
        </span>
      </template>
    </Column>

    <!-- Reason -->
    <Column field="reason" header="Motif" sortable style="min-width: 160px">
      <template #body="slotProps">
        <div>
          <p class="text-sm text-secondary-800">{{ getReasonLabel(slotProps.data.reason) }}</p>
          <p
            v-if="slotProps.data.reason_detail"
            class="text-xs text-gray-400 truncate max-w-[200px]"
            :title="slotProps.data.reason_detail"
          >
            {{ slotProps.data.reason_detail }}
          </p>
        </div>
      </template>
    </Column>

    <!-- Refund Amount -->
    <Column field="refund_amount" header="Montant" sortable style="width: 100px">
      <template #body="slotProps">
        <span v-if="slotProps.data.refund_amount" class="font-semibold text-secondary-900">
          {{ formatCurrency(slotProps.data.refund_amount, slotProps.data.refund_currency) }}
        </span>
        <span v-else class="text-gray-400">-</span>
      </template>
    </Column>

    <!-- Status -->
    <Column field="status" header="Statut" sortable style="width: 140px">
      <template #body="slotProps">
        <Tag
          :value="getStatusLabel(slotProps.data.status)"
          :severity="getStatusSeverity(slotProps.data.status)"
        />
      </template>
    </Column>

    <!-- State -->
    <Column field="state" header="État" sortable style="width: 90px">
      <template #body="slotProps">
        <span
          class="inline-flex items-center gap-1.5 text-xs font-medium"
          :class="slotProps.data.state === 'OPEN' ? 'text-amber-600' : 'text-gray-400'"
        >
          <span
            class="w-2 h-2 rounded-full"
            :class="slotProps.data.state === 'OPEN' ? 'bg-amber-500' : 'bg-gray-300'"
          />
          {{ getStateLabel(slotProps.data.state) }}
        </span>
      </template>
    </Column>

    <!-- Deadline -->
    <Column field="deadline_date" header="Échéance" sortable style="width: 110px">
      <template #body="slotProps">
        <span
          v-if="slotProps.data.deadline_date"
          class="text-sm"
          :class="slotProps.data.is_past_deadline ? 'text-red-500 font-medium' : 'text-gray-600'"
        >
          {{ formatDate(slotProps.data.deadline_date) }}
        </span>
        <span v-else class="text-gray-400">-</span>
      </template>
    </Column>

    <!-- Created Date -->
    <Column field="creation_date" header="Créé le" sortable style="width: 110px">
      <template #body="slotProps">
        <span class="text-sm text-gray-600">
          {{ formatDate(slotProps.data.creation_date) }}
        </span>
      </template>
    </Column>

    <!-- Actions -->
    <Column header="" style="width: 50px">
      <template #body="slotProps">
        <div class="flex gap-1 justify-end">
          <button
            class="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-platform-ebay hover:bg-blue-50 transition-colors"
            title="Voir les détails"
            @click.stop="$emit('view', slotProps.data)"
          >
            <i class="pi pi-eye text-sm" />
          </button>
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { EbayReturn } from '~/types/ebay'
import { formatCurrency, formatDate } from '~/utils/formatters'

defineProps<{
  returns: EbayReturn[]
  totalRecords: number
  currentPage: number
  rowsPerPage: number
  loading: boolean
}>()

defineEmits<{
  page: [event: { page: number; rows: number }]
  'row-click': [event: { data: EbayReturn }]
  view: [returnItem: EbayReturn]
  sync: []
}>()

const { getStatusLabel, getStatusSeverity, getStateLabel, getReasonLabel } = useEbayReturns()
</script>

<style scoped>
:deep(.returns-table) {
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
    cursor: pointer;
  }

  .p-datatable-tbody > tr > td {
    border: none;
    border-bottom: 1px solid #f9fafb;
    padding: 0.75rem 1rem;
    vertical-align: middle;
  }

  .p-datatable-tbody > tr:hover {
    background: #eff6ff !important;
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
    background: #3b82f6;
    color: #ffffff;
    border-color: #3b82f6;
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
}
</style>
