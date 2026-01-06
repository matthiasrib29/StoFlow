<template>
  <div class="page-container">
    <PageHeader
      title="Données de référence"
      subtitle="Gestion des marques, catégories, couleurs et matières"
    />

    <!-- Tabs -->
    <TabView v-model:activeIndex="activeTab" class="admin-tabs">
      <!-- Brands Tab -->
      <TabPanel header="Marques">
        <AttributeTable
          type="brands"
          :columns="brandColumns"
          :items="brands"
          :total="totals.brands"
          :loading="isLoading"
          @refresh="() => loadData('brands')"
          @create="() => openDialog('brands')"
          @edit="(item) => openDialog('brands', item)"
          @delete="(item) => confirmDelete('brands', item)"
        />
      </TabPanel>

      <!-- Categories Tab -->
      <TabPanel header="Categories">
        <AttributeTable
          type="categories"
          :columns="categoryColumns"
          :items="categories"
          :total="totals.categories"
          :loading="isLoading"
          @refresh="() => loadData('categories')"
          @create="() => openDialog('categories')"
          @edit="(item) => openDialog('categories', item)"
          @delete="(item) => confirmDelete('categories', item)"
        />
      </TabPanel>

      <!-- Colors Tab -->
      <TabPanel header="Couleurs">
        <AttributeTable
          type="colors"
          :columns="colorColumns"
          :items="colors"
          :total="totals.colors"
          :loading="isLoading"
          @refresh="() => loadData('colors')"
          @create="() => openDialog('colors')"
          @edit="(item) => openDialog('colors', item)"
          @delete="(item) => confirmDelete('colors', item)"
        />
      </TabPanel>

      <!-- Materials Tab -->
      <TabPanel header="Matieres">
        <AttributeTable
          type="materials"
          :columns="materialColumns"
          :items="materials"
          :total="totals.materials"
          :loading="isLoading"
          @refresh="() => loadData('materials')"
          @create="() => openDialog('materials')"
          @edit="(item) => openDialog('materials', item)"
          @delete="(item) => confirmDelete('materials', item)"
        />
      </TabPanel>
    </TabView>

    <!-- Create/Edit Dialog -->
    <AttributeDialog
      v-if="dialogVisible"
      ref="dialogRef"
      :type="dialogType"
      :item="dialogItem"
      @close="closeDialog"
      @save="handleSave"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import ConfirmDialog from 'primevue/confirmdialog'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AttributeDialog from '~/components/admin/AttributeDialog.vue'
import {
  useAdminAttributes,
  type AttributeType,
  type AdminAttribute,
} from '~/composables/useAdminAttributes'
import { adminLogger } from '~/utils/logger'

definePageMeta({
  layout: 'dashboard',
  middleware: ['admin'],
})

// Composables
const {
  brands,
  categories,
  colors,
  materials,
  totals,
  isLoading,
  fetchAttributes,
  createAttribute,
  updateAttribute,
  deleteAttribute,
} = useAdminAttributes()

const confirm = useConfirm()
const toast = useToast()

// State
const activeTab = ref(0)
const dialogVisible = ref(false)
const dialogType = ref<AttributeType>('brands')
const dialogItem = ref<AdminAttribute | null>(null)
const dialogRef = ref<InstanceType<typeof AttributeDialog> | null>(null)

// Column definitions
const brandColumns = [
  { field: 'name', header: 'Nom (EN)', sortable: true },
  { field: 'name_fr', header: 'Nom (FR)' },
  { field: 'monitoring', header: 'Monitoring', type: 'boolean' },
  { field: 'sector_jeans', header: 'Sector Jeans' },
  { field: 'sector_jacket', header: 'Sector Jacket' },
]

const categoryColumns = [
  { field: 'name_en', header: 'Nom (EN)', sortable: true },
  { field: 'name_fr', header: 'Nom (FR)' },
  { field: 'parent_category', header: 'Parent' },
  { field: 'genders', header: 'Genres', type: 'array' },
]

const colorColumns = [
  { field: 'name_en', header: 'Nom (EN)', sortable: true },
  { field: 'name_fr', header: 'Nom (FR)' },
  { field: 'hex_code', header: 'Couleur', type: 'color' },
]

const materialColumns = [
  { field: 'name_en', header: 'Nom (EN)', sortable: true },
  { field: 'name_fr', header: 'Nom (FR)' },
  { field: 'vinted_id', header: 'Vinted ID' },
]

// Load data for a specific type
const loadData = async (type: AttributeType) => {
  try {
    await fetchAttributes(type, { limit: 100 })
  } catch (e) {
    adminLogger.error(`Failed to load ${type}`, { error: e })
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: `Impossible de charger les ${type}`,
      life: 3000,
    })
  }
}

// Load initial data
const loadAllData = async () => {
  await Promise.all([
    loadData('brands'),
    loadData('categories'),
    loadData('colors'),
    loadData('materials'),
  ])
}

// Dialog handlers
const openDialog = (type: AttributeType, item?: AdminAttribute) => {
  dialogType.value = type
  dialogItem.value = item || null
  dialogVisible.value = true
}

const closeDialog = () => {
  dialogVisible.value = false
  dialogItem.value = null
}

const handleSave = async (data: Record<string, any>) => {
  if (!dialogRef.value) return

  dialogRef.value.setLoading(true)

  try {
    if (dialogItem.value) {
      // Update
      await updateAttribute(dialogType.value, dialogItem.value.pk, data)
      toast.add({
        severity: 'success',
        summary: 'Succes',
        detail: 'Element modifie',
        life: 3000,
      })
    } else {
      // Create
      await createAttribute(dialogType.value, data)
      toast.add({
        severity: 'success',
        summary: 'Succes',
        detail: 'Element cree',
        life: 3000,
      })
    }

    dialogRef.value.close()
    closeDialog()
    await loadData(dialogType.value)
  } catch (e: any) {
    toast.add({
      severity: 'error',
      summary: 'Erreur',
      detail: e.message || 'Operation echouee',
      life: 5000,
    })
  } finally {
    if (dialogRef.value) {
      dialogRef.value.setLoading(false)
    }
  }
}

// Delete handler
const confirmDelete = (type: AttributeType, item: AdminAttribute) => {
  const typeLabels: Record<AttributeType, string> = {
    brands: 'cette marque',
    categories: 'cette categorie',
    colors: 'cette couleur',
    materials: 'cette matiere',
  }

  confirm.require({
    message: `Voulez-vous vraiment supprimer ${typeLabels[type]} ?`,
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Annuler',
    acceptLabel: 'Supprimer',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteAttribute(type, item.pk)
        toast.add({
          severity: 'success',
          summary: 'Succes',
          detail: 'Element supprime',
          life: 3000,
        })
        await loadData(type)
      } catch (e: any) {
        toast.add({
          severity: 'error',
          summary: 'Erreur',
          detail: e.message || 'Impossible de supprimer',
          life: 5000,
        })
      }
    },
  })
}

// Initial load
onMounted(() => {
  loadAllData()
})
</script>

<script lang="ts">
// AttributeTable inline component
// PrimeVue components must be explicitly imported for Options API components
/* eslint-disable import/first */
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import PButton from 'primevue/button'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
/* eslint-enable import/first */

interface ColumnDef {
  field: string
  header: string
  sortable?: boolean
  type?: 'boolean' | 'color' | 'array'
}

const AttributeTable = defineComponent({
  name: 'AttributeTable',
  components: { DataTable, Column, PButton, InputText, Tag },
  props: {
    type: { type: String as PropType<AttributeType>, required: true },
    columns: { type: Array as PropType<ColumnDef[]>, required: true },
    items: { type: Array, required: true },
    total: { type: Number, required: true },
    loading: { type: Boolean, default: false },
  },
  emits: ['refresh', 'create', 'edit', 'delete'],
  setup(props, { emit }) {
    const search = ref('')

    const filteredItems = computed(() => {
      if (!search.value) return props.items
      const term = search.value.toLowerCase()
      return props.items.filter((item: any) => {
        return Object.values(item).some((val) =>
          String(val || '').toLowerCase().includes(term)
        )
      })
    })

    return () =>
      h('div', { class: 'space-y-4' }, [
        // Toolbar
        h('div', { class: 'flex justify-between items-center' }, [
          h('div', { class: 'flex gap-2' }, [
            h(InputText, {
              modelValue: search.value,
              'onUpdate:modelValue': (v: string) => (search.value = v),
              placeholder: 'Rechercher...',
              class: 'w-64',
            }),
            h(PButton, {
              icon: 'pi pi-refresh',
              severity: 'secondary',
              onClick: () => emit('refresh'),
            }),
          ]),
          h(PButton, {
            label: 'Nouveau',
            icon: 'pi pi-plus',
            onClick: () => emit('create'),
          }),
        ]),

        // Table
        h(
          DataTable,
          {
            value: filteredItems.value,
            loading: props.loading,
            paginator: true,
            rows: 20,
            rowsPerPageOptions: [10, 20, 50],
            stripedRows: true,
            dataKey: 'pk',
            pt: { root: { class: 'border-0' } },
          },
          {
            empty: () =>
              h('div', { class: 'text-center py-8 text-gray-500' }, [
                h('i', { class: 'pi pi-inbox text-4xl mb-3 block' }),
                h('p', 'Aucun element trouve'),
              ]),
            default: () => [
              ...props.columns.map((col) =>
                h(
                  Column,
                  {
                    field: col.field,
                    header: col.header,
                    sortable: col.sortable,
                    style: 'min-width: 100px',
                  },
                  col.type === 'boolean'
                    ? {
                        body: ({ data }: any) =>
                          h(Tag, {
                            value: data[col.field] ? 'Oui' : 'Non',
                            severity: data[col.field] ? 'success' : 'secondary',
                          }),
                      }
                    : col.type === 'color'
                    ? {
                        body: ({ data }: any) =>
                          data[col.field]
                            ? h('div', { class: 'flex items-center gap-2' }, [
                                h('div', {
                                  class: 'w-6 h-6 rounded border',
                                  style: { backgroundColor: data[col.field] },
                                }),
                                h('span', { class: 'text-sm' }, data[col.field]),
                              ])
                            : h('span', { class: 'text-gray-400' }, '-'),
                      }
                    : col.type === 'array'
                    ? {
                        body: ({ data }: any) =>
                          data[col.field]?.length
                            ? h(
                                'div',
                                { class: 'flex gap-1 flex-wrap' },
                                data[col.field].map((v: string) =>
                                  h(Tag, { value: v, severity: 'info', class: 'text-xs' })
                                )
                              )
                            : h('span', { class: 'text-gray-400' }, '-'),
                      }
                    : {
                        body: ({ data }: any) =>
                          h(
                            'span',
                            { class: data[col.field] ? '' : 'text-gray-400' },
                            data[col.field] || '-'
                          ),
                      }
                )
              ),
              // Actions column
              h(
                Column,
                { header: 'Actions', style: 'width: 120px' },
                {
                  body: ({ data }: any) =>
                    h('div', { class: 'flex gap-1' }, [
                      h(PButton, {
                        icon: 'pi pi-pencil',
                        severity: 'secondary',
                        text: true,
                        size: 'small',
                        onClick: () => emit('edit', data),
                      }),
                      h(PButton, {
                        icon: 'pi pi-trash',
                        severity: 'danger',
                        text: true,
                        size: 'small',
                        onClick: () => emit('delete', data),
                      }),
                    ]),
                }
              ),
            ],
          }
        ),

        // Footer
        h('div', { class: 'text-sm text-gray-500' }, `${props.total} elements au total`),
      ])
  },
})

export default {
  components: {
    AttributeTable,
  },
}
</script>

<style scoped>
.page-container {
  @apply p-6 lg:p-8;
}

:deep(.admin-tabs .p-tabview-panels) {
  @apply p-0;
}

:deep(.admin-tabs .p-tabview-panel) {
  @apply pt-4;
}
</style>
