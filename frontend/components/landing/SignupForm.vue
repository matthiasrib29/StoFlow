<template>
  <div class="signup-form-wrapper">
    <form @submit.prevent="handleSubmit" class="signup-form">
      <!-- Email (toujours visible) -->
      <div class="form-group">
        <InputText
          v-model="formData.email"
          type="email"
          placeholder="Votre email"
          class="form-input"
          :class="{ 'p-invalid': errors.email }"
          required
        />
        <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
      </div>

      <!-- Champs supplémentaires (optionnels) -->
      <template v-if="showFullForm">
        <div class="form-group">
          <InputText
            v-model="formData.firstName"
            type="text"
            placeholder="Votre prénom (optionnel)"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <Dropdown
            v-model="formData.vendorType"
            :options="vendorTypes"
            option-label="label"
            option-value="value"
            placeholder="Type de vendeur (optionnel)"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <Dropdown
            v-model="formData.monthlyVolume"
            :options="monthlyVolumes"
            option-label="label"
            option-value="value"
            placeholder="Volume mensuel (optionnel)"
            class="form-input"
          />
        </div>
      </template>

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
        ✅ {{ successMessage }}
      </div>
      <div v-if="errorMessage" class="message error-message">
        ❌ {{ errorMessage }}
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
  firstName: '',
  vendorType: null as string | null,
  monthlyVolume: null as string | null
})

const vendorTypes = [
  { label: 'Particulier', value: 'particular' },
  { label: 'Semi-pro', value: 'semi-pro' },
  { label: 'Pro', value: 'pro' }
]

const monthlyVolumes = [
  { label: 'Moins de 10', value: '<10' },
  { label: '10-50', value: '10-50' },
  { label: '50-200', value: '50-200' },
  { label: 'Plus de 200', value: '200+' }
]

const errors = reactive({
  email: ''
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
  successMessage.value = ''
  errorMessage.value = ''

  // Validate email
  if (!formData.email) {
    errors.email = 'Email requis'
    return
  }

  if (!validateEmail(formData.email)) {
    errors.email = 'Email invalide'
    return
  }

  isLoading.value = true

  try {
    const response = await $fetch('/api/beta/signup', {
      method: 'POST',
      body: {
        email: formData.email,
        first_name: formData.firstName || null,
        vendor_type: formData.vendorType,
        monthly_volume: formData.monthlyVolume
      }
    })

    // Success!
    successMessage.value = 'Inscription réussie !'

    // Decrement places counter
    if (placesRestantes && placesRestantes.value > 0) {
      placesRestantes.value--
      localStorage.setItem('placesRestantes', placesRestantes.value.toString())
    }

    // Redirect to thank you page
    setTimeout(() => {
      navigateTo('/merci')
    }, 1000)
  } catch (error: any) {
    console.error('Signup error:', error)

    if (error.statusCode === 400) {
      errorMessage.value = error.statusMessage || 'Cet email est déjà inscrit.'
    } else {
      errorMessage.value = 'Une erreur est survenue. Veuillez réessayer.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.signup-form-wrapper {
  max-width: 500px;
  margin: 0 auto;
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
}

.success-message {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #22c55e;
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

:deep(.p-error) {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

@media (max-width: 768px) {
  .form-input {
    font-size: 0.95rem;
    padding: 0.75rem 1rem;
  }

  .submit-button {
    font-size: 1rem;
  }
}
</style>
