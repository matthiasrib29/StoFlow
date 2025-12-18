<template>
  <Card class="shadow-md">
    <template #title>
      <div class="flex items-center gap-2">
        <i class="pi pi-bolt text-primary-500"></i>
        <span class="text-secondary-900 font-bold">Actions rapides</span>
      </div>
    </template>
    <template #content>
      <div v-auto-animate class="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-grid-fast">
        <button
          v-for="action in actions"
          :key="action.label"
          @click="handleAction(action.action)"
          class="flex flex-col items-center gap-3 p-4 rounded-lg hover:bg-primary-50 transition group"
        >
          <div :class="[
            'w-12 h-12 rounded-full flex items-center justify-center transition',
            action.bgColor,
            'group-hover:scale-110'
          ]">
            <i :class="[action.icon, 'text-2xl', action.iconColor]"></i>
          </div>
          <span class="text-sm font-bold text-secondary-900 text-center">
            {{ action.label }}
          </span>
        </button>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
const router = useRouter()

interface QuickAction {
  label: string
  icon: string
  bgColor: string
  iconColor: string
  action: string
}

const actions: QuickAction[] = [
  {
    label: 'Créer un produit',
    icon: 'pi-plus-circle',
    bgColor: 'bg-primary-100',
    iconColor: 'text-primary-600',
    action: 'create-product'
  },
  {
    label: 'Publier un produit',
    icon: 'pi-send',
    bgColor: 'bg-primary-100',
    iconColor: 'text-primary-600',
    action: 'publish-product'
  },
  {
    label: 'Voir les publications',
    icon: 'pi-list',
    bgColor: 'bg-primary-100',
    iconColor: 'text-primary-600',
    action: 'view-publications'
  },
  {
    label: 'Gérer les intégrations',
    icon: 'pi-link',
    bgColor: 'bg-primary-100',
    iconColor: 'text-primary-600',
    action: 'manage-integrations'
  }
]

const handleAction = (action: string) => {
  switch (action) {
    case 'create-product':
      router.push('/dashboard/products/create')
      break
    case 'publish-product':
      router.push('/dashboard/products')
      break
    case 'view-publications':
      router.push('/dashboard/publications')
      break
    case 'manage-integrations':
      router.push('/dashboard/settings')
      break
  }
}
</script>
