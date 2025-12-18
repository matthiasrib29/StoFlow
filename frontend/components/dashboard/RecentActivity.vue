<template>
  <Card class="shadow-md">
    <template #title>
      <div class="flex items-center gap-2">
        <i class="pi pi-clock text-primary-500"/>
        <span class="text-secondary-900 font-bold">Activité récente</span>
      </div>
    </template>
    <template #content>
      <div v-if="isLoading" class="text-center py-8">
        <i class="pi pi-spin pi-spinner text-3xl text-primary-500"/>
      </div>

      <div v-else-if="activities.length === 0" class="text-center py-8">
        <i class="pi pi-inbox text-4xl text-gray-400 mb-3"/>
        <p class="text-gray-500">Aucune activité récente</p>
      </div>

      <div v-else v-auto-animate class="space-y-4">
        <div
          v-for="activity in activities"
          :key="activity.id"
          class="flex items-start gap-4 p-3 rounded-lg hover:bg-gray-50 transition"
        >
          <div
:class="[
            'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
            getActivityBgColor(activity.color)
          ]">
            <i :class="[activity.icon, 'text-lg', getActivityTextColor(activity.color)]"/>
          </div>

          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-secondary-900">{{ activity.title }}</p>
            <p class="text-sm text-secondary-600 truncate">{{ activity.description }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ formatTime(activity.timestamp) }}</p>
          </div>
        </div>
      </div>

      <div v-if="activities.length > 0" class="mt-4 pt-4 border-t border-gray-200 text-center">
        <NuxtLink
          to="/dashboard/activity"
          class="text-sm font-bold text-primary-600 hover:text-primary-700"
        >
          Voir toute l'activité
          <i class="pi pi-arrow-right ml-1"/>
        </NuxtLink>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
const publicationsStore = usePublicationsStore()

const activities = computed(() => publicationsStore.recentActivity)
const isLoading = computed(() => publicationsStore.isLoading)

const getActivityBgColor = (color: string): string => {
  const colors: Record<string, string> = {
    green: 'bg-primary-100',
    blue: 'bg-primary-100',
    primary: 'bg-primary-100',
    orange: 'bg-primary-100',
    red: 'bg-secondary-100'
  }
  return colors[color] || 'bg-gray-100'
}

const getActivityTextColor = (color: string): string => {
  const colors: Record<string, string> = {
    green: 'text-primary-600',
    blue: 'text-primary-600',
    primary: 'text-primary-600',
    orange: 'text-primary-600',
    red: 'text-secondary-600'
  }
  return colors[color] || 'text-gray-600'
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'À l\'instant'
  if (diffMins < 60) return `Il y a ${diffMins} min`
  if (diffHours < 24) return `Il y a ${diffHours}h`
  if (diffDays < 7) return `Il y a ${diffDays}j`

  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

// Charger l'activité au montage
onMounted(() => {
  publicationsStore.fetchRecentActivity()
})
</script>
