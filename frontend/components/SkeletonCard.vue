<template>
  <div
    :class="['skeleton-card', cardClass]"
    :style="cardStyle"
  >
    <!-- Image skeleton -->
    <div
      v-if="showImage"
      class="skeleton skeleton-image"
      :style="{ height: imageHeight }"
    ></div>

    <!-- Content skeleton -->
    <div :class="['skeleton-content', contentClass]">
      <!-- Title -->
      <div
        class="skeleton skeleton-title"
        :style="{ width: titleWidth, height: titleHeight }"
      ></div>

      <!-- Lines -->
      <div
        v-for="(width, index) in lineWidths"
        :key="index"
        class="skeleton skeleton-line"
        :style="{ width, height: lineHeight, marginTop: lineSpacing }"
      ></div>

      <!-- Actions/Buttons skeleton -->
      <div v-if="showActions" class="skeleton-actions">
        <div
          v-for="n in actionsCount"
          :key="n"
          class="skeleton skeleton-action"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  /** Afficher l'image skeleton (défaut: true) */
  showImage?: boolean
  /** Hauteur de l'image (défaut: 200px) */
  imageHeight?: string
  /** Largeur du titre (défaut: 70%) */
  titleWidth?: string
  /** Hauteur du titre (défaut: 24px) */
  titleHeight?: string
  /** Nombre de lignes de texte (défaut: 3) */
  lines?: number
  /** Largeurs personnalisées des lignes (surcharge lines) */
  lineWidths?: string[]
  /** Hauteur des lignes (défaut: 16px) */
  lineHeight?: string
  /** Espacement entre lignes (défaut: 12px) */
  lineSpacing?: string
  /** Afficher les actions/boutons (défaut: false) */
  showActions?: boolean
  /** Nombre de boutons (défaut: 2) */
  actionsCount?: number
  /** Classes CSS additionnelles pour la carte */
  cardClass?: string
  /** Styles inline pour la carte */
  cardStyle?: Record<string, string>
  /** Classes CSS pour le contenu */
  contentClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  showImage: true,
  imageHeight: '200px',
  titleWidth: '70%',
  titleHeight: '24px',
  lines: 3,
  lineHeight: '16px',
  lineSpacing: '12px',
  showActions: false,
  actionsCount: 2,
  cardClass: '',
  cardStyle: () => ({}),
  contentClass: ''
})

// Générer les largeurs des lignes si non fournies
const lineWidths = computed(() => {
  if (props.lineWidths && props.lineWidths.length > 0) {
    return props.lineWidths
  }

  // Générer des largeurs variées pour un effet réaliste
  const widths: string[] = []
  for (let i = 0; i < props.lines; i++) {
    if (i === props.lines - 1) {
      // Dernière ligne plus courte
      widths.push('60%')
    } else {
      // Lignes complètes avec légère variation
      widths.push(['100%', '95%', '90%'][i % 3])
    }
  }
  return widths
})
</script>

<style scoped>
.skeleton-card {
  @apply bg-white rounded-xl overflow-hidden shadow-sm;
}

.skeleton-content {
  @apply p-4 space-y-3;
}

/* Image skeleton */
.skeleton-image {
  @apply w-full;
}

/* Title skeleton */
.skeleton-title {
  @apply rounded-md;
}

/* Line skeleton */
.skeleton-line {
  @apply rounded;
}

/* Actions skeleton */
.skeleton-actions {
  @apply flex gap-3 mt-4 pt-4 border-t border-gray-100;
}

.skeleton-action {
  @apply h-10 rounded-lg flex-1;
}

/* Animation pulse déjà définie dans modern-dashboard.css (.skeleton) */
</style>
