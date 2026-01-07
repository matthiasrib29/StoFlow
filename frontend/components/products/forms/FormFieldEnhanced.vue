<template>
  <div class="form-field-enhanced">
    <label
      v-if="label"
      :for="fieldId"
      class="form-label flex items-center gap-2"
    >
      <span>{{ label }}</span>
      <span
        v-if="required"
        class="text-error-600"
        :style="{ fontSize: 'var(--form-required-size)' }"
        aria-label="Champ requis"
      >*</span>
      <i
        v-if="isValid"
        class="pi pi-check-circle text-success-600"
        :style="{ fontSize: 'var(--form-checkmark-size)' }"
        aria-label="Champ valide"
      />
    </label>

    <slot />

    <small
      v-if="helperText && !hasError"
      class="form-helper-text block"
    >
      {{ helperText }}
    </small>

    <Transition name="error-message">
      <small
        v-if="hasError && errorMessage"
        class="form-error-message"
        role="alert"
      >
        <i class="pi pi-exclamation-circle" />
        <span>{{ errorMessage }}</span>
      </small>
    </Transition>
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
  fieldId?: string
}

withDefaults(defineProps<Props>(), {
  label: undefined,
  required: false,
  helperText: undefined,
  hasError: false,
  errorMessage: undefined,
  isValid: false,
  fieldId: undefined
})
</script>

<style scoped>
.form-field-enhanced {
  margin-bottom: var(--form-spacing-field);
}

.form-helper-text {
  font-size: var(--form-helper-size);
  color: #6a6a6a;
  margin-top: 4px;
}

.form-error-message {
  font-size: var(--form-helper-size);
  color: var(--form-error-color);
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.error-message-enter-active {
  animation: slide-down 0.3s ease-out;
}

.error-message-leave-active {
  animation: slide-up 0.2s ease-in;
}

@keyframes slide-down {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slide-up {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-5px);
  }
}
</style>
