<template>
  <div class="flex items-center gap-2">
    <Select
      v-model="selectedLocale"
      :options="localeOptions"
      optionLabel="label"
      optionValue="code"
      @change="handleLocaleChange"
      class="min-w-[160px]"
    >
      <template #value="slotProps">
        <div v-if="slotProps.value" class="flex items-center gap-2">
          <span class="text-xl">{{ getCurrentFlag(slotProps.value) }}</span>
          <span class="font-medium text-secondary-900">{{ getCurrentLabel(slotProps.value) }}</span>
        </div>
      </template>
      <template #option="slotProps">
        <div class="flex items-center gap-2 py-1">
          <span class="text-xl">{{ slotProps.option.flag }}</span>
          <span class="font-medium">{{ slotProps.option.label }}</span>
        </div>
      </template>
    </Select>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useLocaleStore, AVAILABLE_LOCALES, type SupportedLocale } from '~/stores/locale'
import { useAttributes } from '~/composables/useAttributes'

const localeStore = useLocaleStore()
const { clearCache } = useAttributes()

// Locale sélectionnée
const selectedLocale = computed({
  get: () => localeStore.locale,
  set: (value: SupportedLocale) => localeStore.setLocale(value)
})

// Options de langue
const localeOptions = AVAILABLE_LOCALES

// Récupérer le drapeau de la locale courante
const getCurrentFlag = (code: SupportedLocale) => {
  return AVAILABLE_LOCALES.find(l => l.code === code)?.flag || '🌐'
}

// Récupérer le label de la locale courante
const getCurrentLabel = (code: SupportedLocale) => {
  return AVAILABLE_LOCALES.find(l => l.code === code)?.label || 'Language'
}

// Gérer le changement de langue
const handleLocaleChange = () => {
  // Vider le cache des attributs pour forcer le rechargement dans la nouvelle langue
  clearCache()

  // Optionnel : rafraîchir la page pour recharger tous les composants
  // location.reload()
}
</script>
