<template>
  <div>
    <!-- Label -->
    <label
      v-if="label"
      class="block text-xs font-semibold mb-1 text-secondary-900 flex items-center gap-1"
    >
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
      <i
        v-if="isValid"
        class="pi pi-check-circle text-green-500 text-xs"
      />
    </label>

    <!-- Field Content (slot) -->
    <slot />

    <!-- Helper Text -->
    <small v-if="helperText && !hasError" class="text-xs text-gray-500 block mt-1">
      {{ helperText }}
    </small>

    <!-- Error Message -->
    <small v-if="hasError && errorMessage" class="p-error block mt-1">
      {{ errorMessage }}
    </small>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label?: string
  required?: boolean
  helperText?: string
  hasError?: boolean
  errorMessage?: string
  isValid?: boolean
}

withDefaults(defineProps<Props>(), {
  label: undefined,
  required: false,
  helperText: undefined,
  hasError: false,
  errorMessage: undefined,
  isValid: false
})
</script>
