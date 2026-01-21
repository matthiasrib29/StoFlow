<template>
  <div class="signup-form-wrapper">
    <form @submit.prevent="handleSubmit" class="signup-form">
      <!-- Email (toujours visible) -->
      <div class="form-group">
        <InputText
          v-model="formData.email"
          type="email"
          placeholder="Votre email *"
          class="form-input"
          :class="{ 'p-invalid': errors.email }"
          required
        />
        <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
      </div>

      <!-- Champs supplémentaires (obligatoires) -->
      <template v-if="showFullForm">
        <div class="form-group">
          <InputText
            v-model="formData.name"
            type="text"
            placeholder="Votre nom complet *"
            class="form-input"
            :class="{ 'p-invalid': errors.name }"
            required
          />
          <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
        </div>

        <div class="form-group">
          <Dropdown
            v-model="formData.vendorType"
            :options="vendorTypes"
            option-label="label"
            option-value="value"
            placeholder="Type de vendeur *"
            class="w-full"
            :class="{ 'p-invalid': errors.vendorType }"
          />
          <small v-if="errors.vendorType" class="p-error">{{ errors.vendorType }}</small>
        </div>

        <div class="form-group">
          <Dropdown
            v-model="formData.productCount"
            :options="productCounts"
            option-label="label"
            option-value="value"
            placeholder="Combien de produits avez-vous ? *"
            class="w-full"
            :class="{ 'p-invalid': errors.productCount }"
          />
          <small v-if="errors.productCount" class="p-error">{{ errors.productCount }}</small>
        </div>
      </template>

      <!-- Honeypot field - invisible to humans, bots fill it -->
      <!-- Security Fix 2026-01-20: Anti-spam protection -->
      <div class="honeypot-field" aria-hidden="true">
        <label for="website">Website (leave empty)</label>
        <input
          v-model="formData.website"
          type="text"
          name="website"
          id="website"
          tabindex="-1"
          autocomplete="off"
        />
      </div>

      <!-- Submit button -->
      <Button
        type="submit"
        :label="isLoading ? 'Inscription...' : 'Rejoindre la beta gratuite'"
        :loading="isLoading"
        class="submit-button"
        :disabled="isLoading"
      />

      <!-- Success/Error messages -->
      <div v-if="successMessage" class="message success-message">
        <i class="pi pi-check-circle"></i>
        <span>{{ successMessage }}</span>
      </div>
      <div v-if="errorMessage" class="message error-message">
        <i class="pi pi-times-circle"></i>
        <span>{{ errorMessage }}</span>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
interface Props {
  showFullForm?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showFullForm: true
})

const formData = reactive({
  email: '',
  name: '',
  vendorType: null as string | null,
  productCount: null as string | null,
  website: '' // Honeypot field - should remain empty
})

const vendorTypes = [
  { label: 'Particulier', value: 'particulier' },
  { label: 'Professionnel', value: 'professionnel' }
]

const productCounts = [
  { label: 'Moins de 100', value: '0-100' },
  { label: 'Entre 100 et 1000', value: '100-1000' },
  { label: 'Plus de 1000', value: '1000+' }
]

const errors = reactive({
  email: '',
  name: '',
  vendorType: '',
  productCount: ''
})

const isLoading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Inject places counter
const placesRestantes = inject<Ref<number>>('placesRestantes')

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleSubmit = async () => {
  // Reset messages
  errors.email = ''
  errors.name = ''
  errors.vendorType = ''
  errors.productCount = ''
  successMessage.value = ''
  errorMessage.value = ''

  let hasError = false

  // Validate email
  if (!formData.email) {
    errors.email = 'Email requis'
    hasError = true
  } else if (!validateEmail(formData.email)) {
    errors.email = 'Email invalide'
    hasError = true
  }

  // Validate name (if full form is shown)
  if (props.showFullForm && !formData.name) {
    errors.name = 'Nom requis'
    hasError = true
  }

  // Validate vendor type (if full form is shown)
  if (props.showFullForm && !formData.vendorType) {
    errors.vendorType = 'Type de vendeur requis'
    hasError = true
  }

  // Validate product count (if full form is shown)
  if (props.showFullForm && !formData.productCount) {
    errors.productCount = 'Nombre de produits requis'
    hasError = true
  }

  if (hasError) return

  isLoading.value = true

  try {
    const response = await $fetch('/api/beta/signup', {
      method: 'POST',
      body: {
        email: formData.email,
        name: formData.name || 'Anonyme',
        vendor_type: formData.vendorType || 'particulier',
        product_count: formData.productCount || '0-100',
        website: formData.website || null  // Honeypot field
      }
    })

    // Success!
    successMessage.value = 'Inscription réussie ! Vérifiez votre email.'

    // Decrement places counter (minimum 15)
    const PLACES_MIN = 15
    if (placesRestantes && placesRestantes.value > PLACES_MIN) {
      placesRestantes.value--
      localStorage.setItem('placesRestantes', placesRestantes.value.toString())
    }

    // Redirect to thank you page
    setTimeout(() => {
      navigateTo('/merci')
    }, 1500)
  } catch (error: any) {
    console.error('Signup error:', error)

    if (error.statusCode === 409 || error.statusCode === 400) {
      errorMessage.value = 'Cette adresse email est déjà inscrite à la beta.'
    } else {
      errorMessage.value = 'Une erreur est survenue. Veuillez réessayer.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* Honeypot field - hidden from humans, bots fill it */
/* Security Fix 2026-01-20: Anti-spam protection */
.honeypot-field {
  position: absolute;
  left: -9999px;
  top: -9999px;
  opacity: 0;
  pointer-events: none;
  height: 0;
  width: 0;
  overflow: hidden;
}

.signup-form-wrapper {
  max-width: 500px;
  margin: 0 auto;
  position: relative; /* For honeypot absolute positioning */
}

.signup-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  width: 100%;
}

.form-input {
  width: 100%;
  padding: 0.875rem 1.25rem;
  font-size: 1rem;
  border-radius: 0.5rem;
}

.submit-button {
  width: 100%;
  padding: 1rem 2rem;
  font-size: 1.125rem;
  font-weight: 700;
  background: #facc15;
  border: none;
  color: #1a1a1a;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.submit-button:hover:not(:disabled) {
  background: #eab308;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(250, 204, 21, 0.3);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.message {
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.success-message {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.success-message i {
  color: #22c55e;
  font-size: 1.25rem;
}

.error-message {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.error-message i {
  color: #ef4444;
  font-size: 1.25rem;
}

:deep(.p-error) {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

@media (max-width: 768px) {
  .signup-form-wrapper {
    max-width: 100%;
  }

  .signup-form {
    gap: 0.875rem;
  }

  .form-input {
    font-size: 1rem;
    padding: 0.875rem 1rem;
    min-height: 48px;
  }

  .submit-button {
    font-size: 1rem;
    padding: 0.875rem 1.5rem;
    min-height: 48px;
  }

  .message {
    padding: 0.875rem;
    font-size: 0.875rem;
  }

  :deep(.p-error) {
    font-size: 0.8125rem;
  }
}
</style>
