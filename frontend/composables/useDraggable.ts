import { ref, type Ref } from 'vue'

/**
 * Composable pour gérer le drag-and-drop avec animations
 * Utilisable pour réorganiser des photos, listes, etc.
 *
 * @example
 * ```typescript
 * const { items, dragStart, dragOver, dragEnd, drop } = useDraggable(photos)
 *
 * <div
 *   v-for="(item, index) in items"
 *   :key="item.id"
 *   draggable="true"
 *   @dragstart="dragStart(index, $event)"
 *   @dragover.prevent="dragOver(index, $event)"
 *   @dragend="dragEnd"
 *   @drop="drop(index, $event)"
 *   :class="{ 'dragging': draggedIndex === index, 'drag-over': dragOverIndex === index }"
 * />
 * ```
 */

export interface DraggableOptions {
  /** Callback appelé après réorganisation */
  onReorder?: (items: any[], fromIndex: number, toIndex: number) => void
  /** Durée de l'animation de transition (ms) */
  animationDuration?: number
  /** Autoriser le drag sur mobile (touch events) */
  enableTouch?: boolean
}

export function useDraggable<T>(
  initialItems: Ref<T[]> | T[],
  options: DraggableOptions = {}
) {
  const { onReorder, animationDuration = 300, enableTouch = true } = options

  // État interne
  const items = ref<T[]>(
    Array.isArray(initialItems) ? initialItems : initialItems.value
  ) as Ref<T[]>

  const draggedIndex = ref<number | null>(null)
  const dragOverIndex = ref<number | null>(null)
  const isDragging = ref(false)

  // Données de drag pour touch
  let touchStartY = 0
  let touchStartX = 0
  let touchElement: HTMLElement | null = null

  /**
   * Démarrer le drag
   */
  const dragStart = (index: number, event: DragEvent) => {
    draggedIndex.value = index
    isDragging.value = true

    // Set data pour le drag
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', String(index))

      // Créer une image de drag personnalisée si possible
      const target = event.target as HTMLElement
      if (target) {
        // Légère rotation pour effet visuel
        target.style.opacity = '0.8'
      }
    }
  }

  /**
   * Pendant le drag-over
   */
  const dragOver = (index: number, event: DragEvent) => {
    event.preventDefault()

    if (draggedIndex.value === null || draggedIndex.value === index) {
      return
    }

    dragOverIndex.value = index

    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move'
    }
  }

  /**
   * Quitter la zone de drop
   */
  const dragLeave = () => {
    dragOverIndex.value = null
  }

  /**
   * Fin du drag (avec ou sans drop)
   */
  const dragEnd = (event?: DragEvent) => {
    // Restaurer l'opacité
    if (event?.target) {
      const target = event.target as HTMLElement
      target.style.opacity = '1'
    }

    isDragging.value = false
    draggedIndex.value = null
    dragOverIndex.value = null
  }

  /**
   * Drop - réorganise les items
   */
  const drop = (targetIndex: number, event: DragEvent) => {
    event.preventDefault()

    if (draggedIndex.value === null || draggedIndex.value === targetIndex) {
      dragEnd()
      return
    }

    // Réorganiser le tableau
    const fromIndex = draggedIndex.value
    const toIndex = targetIndex
    const itemsCopy = [...items.value]
    const [movedItem] = itemsCopy.splice(fromIndex, 1)
    itemsCopy.splice(toIndex, 0, movedItem)

    items.value = itemsCopy

    // Callback
    if (onReorder) {
      onReorder(itemsCopy, fromIndex, toIndex)
    }

    dragEnd()
  }

  /**
   * Déplacer un item programmatiquement
   */
  const moveItem = (fromIndex: number, toIndex: number) => {
    if (fromIndex < 0 || fromIndex >= items.value.length) return
    if (toIndex < 0 || toIndex >= items.value.length) return
    if (fromIndex === toIndex) return

    const itemsCopy = [...items.value]
    const [movedItem] = itemsCopy.splice(fromIndex, 1)
    itemsCopy.splice(toIndex, 0, movedItem)

    items.value = itemsCopy

    if (onReorder) {
      onReorder(itemsCopy, fromIndex, toIndex)
    }
  }

  // ========== Touch Support ==========

  /**
   * Touch start
   */
  const touchStart = (index: number, event: TouchEvent) => {
    if (!enableTouch) return

    const touch = event.touches[0]
    touchStartY = touch.clientY
    touchStartX = touch.clientX
    touchElement = event.target as HTMLElement
    draggedIndex.value = index
    isDragging.value = true

    // Ajouter classe dragging
    if (touchElement) {
      touchElement.classList.add('dragging')
    }
  }

  /**
   * Touch move
   */
  const touchMove = (event: TouchEvent) => {
    if (!enableTouch || !isDragging.value || !touchElement) return

    event.preventDefault()

    const touch = event.touches[0]
    const deltaY = touch.clientY - touchStartY
    const deltaX = touch.clientX - touchStartX

    // Déplacer visuellement l'élément
    touchElement.style.transform = `translate(${deltaX}px, ${deltaY}px)`

    // Trouver l'élément sous le doigt
    const elementsUnder = document.elementsFromPoint(touch.clientX, touch.clientY)
    const dropTarget = elementsUnder.find(el =>
      el.hasAttribute('data-draggable-index') &&
      el !== touchElement
    ) as HTMLElement

    if (dropTarget) {
      const targetIndex = parseInt(dropTarget.getAttribute('data-draggable-index') || '-1')
      if (targetIndex >= 0) {
        dragOverIndex.value = targetIndex
      }
    } else {
      dragOverIndex.value = null
    }
  }

  /**
   * Touch end
   */
  const touchEnd = () => {
    if (!enableTouch || !isDragging.value) return

    // Effectuer le drop si sur une cible
    if (dragOverIndex.value !== null && draggedIndex.value !== null) {
      const fromIndex = draggedIndex.value
      const toIndex = dragOverIndex.value

      if (fromIndex !== toIndex) {
        const itemsCopy = [...items.value]
        const [movedItem] = itemsCopy.splice(fromIndex, 1)
        itemsCopy.splice(toIndex, 0, movedItem)
        items.value = itemsCopy

        if (onReorder) {
          onReorder(itemsCopy, fromIndex, toIndex)
        }
      }
    }

    // Reset
    if (touchElement) {
      touchElement.classList.remove('dragging')
      touchElement.style.transform = ''
    }

    touchElement = null
    isDragging.value = false
    draggedIndex.value = null
    dragOverIndex.value = null
  }

  return {
    items,
    draggedIndex,
    dragOverIndex,
    isDragging,
    // Mouse events
    dragStart,
    dragOver,
    dragLeave,
    dragEnd,
    drop,
    // Touch events
    touchStart,
    touchMove,
    touchEnd,
    // Programmatic
    moveItem
  }
}
