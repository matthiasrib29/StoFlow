# Implémentation du Formulaire d'Onboarding Complet

## 📊 État d'avancement

### ✅ Complété (Backend)
1. ✅ Modèle User mis à jour avec nouveaux champs (models/public/user.py)
   - Enums: AccountType, BusinessType, EstimatedProducts
   - Champs: business_name, account_type, business_type, estimated_products
   - Champs pro: siret, vat_number
   - Contact: phone, country, language

2. ✅ Schéma RegisterRequest mis à jour (schemas/auth_schemas.py)
   - Tous les nouveaux champs ajoutés
   - Validateurs pour account_type, business_type, estimated_products, siret
   - Exemples pour Particulier et Professionnel

### 🔄 En cours

3. ⏳ Endpoint /register à modifier (api/auth.py)
4. ⏳ Script SQL de migration à créer
5. ⏳ Store auth frontend à mettre à jour
6. ⏳ Formulaire d'inscription frontend à créer

---

## 🔧 Modifications restantes

### 1. Endpoint /register (Backend)

**Fichier:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/api/auth.py`

**Changements nécessaires:**

```python
# Ligne ~80-120 (dans la fonction register)

# AVANT (ancien code)
new_user = User(
    email=request.email,
    hashed_password=hashed_password,
    full_name=request.full_name,
    role=UserRole.USER,
)

# APRÈS (nouveau code)
from models.public.user import AccountType, BusinessType, EstimatedProducts

new_user = User(
    email=request.email,
    hashed_password=hashed_password,
    full_name=request.full_name,
    role=UserRole.USER,

    # Onboarding fields (Added: 2024-12-08)
    business_name=request.business_name,
    account_type=AccountType(request.account_type),
    business_type=BusinessType(request.business_type) if request.business_type else None,
    estimated_products=EstimatedProducts(request.estimated_products) if request.estimated_products else None,

    # Professional fields
    siret=request.siret,
    vat_number=request.vat_number,

    # Contact fields
    phone=request.phone,
    country=request.country,
    language=request.language,
)
```

---

### 2. Script SQL de Migration

**Fichier à créer:** `/home/maribeiro/Stoflow/Stoflow_BackEnd/migrations/add_onboarding_fields.sql`

```sql
-- Migration: Ajout des champs d'onboarding au User
-- Date: 2024-12-08
-- Description: Ajoute business_name, account_type, business_type, etc.

-- 1. Créer les ENUMs
CREATE TYPE account_type AS ENUM ('individual', 'professional');
CREATE TYPE business_type AS ENUM ('resale', 'dropshipping', 'artisan', 'retail', 'other');
CREATE TYPE estimated_products AS ENUM ('0-50', '50-200', '200-500', '500+');

-- 2. Ajouter les colonnes à la table users (schema public)
ALTER TABLE public.users
ADD COLUMN business_name VARCHAR(255),
ADD COLUMN account_type account_type NOT NULL DEFAULT 'individual',
ADD COLUMN business_type business_type,
ADD COLUMN estimated_products estimated_products,
ADD COLUMN siret VARCHAR(14),
ADD COLUMN vat_number VARCHAR(20),
ADD COLUMN phone VARCHAR(20),
ADD COLUMN country VARCHAR(2) NOT NULL DEFAULT 'FR',
ADD COLUMN language VARCHAR(2) NOT NULL DEFAULT 'fr';

-- 3. Ajouter les commentaires
COMMENT ON COLUMN public.users.business_name IS 'Nom de l''entreprise ou de la boutique';
COMMENT ON COLUMN public.users.account_type IS 'Type de compte: individual (particulier) ou professional (entreprise)';
COMMENT ON COLUMN public.users.business_type IS 'Type d''activité: resale, dropshipping, artisan, retail, other';
COMMENT ON COLUMN public.users.estimated_products IS 'Nombre de produits estimé: 0-50, 50-200, 200-500, 500+';
COMMENT ON COLUMN public.users.siret IS 'Numéro SIRET (France) - uniquement pour les professionnels';
COMMENT ON COLUMN public.users.vat_number IS 'Numéro de TVA intracommunautaire - uniquement pour les professionnels';
COMMENT ON COLUMN public.users.phone IS 'Numéro de téléphone';
COMMENT ON COLUMN public.users.country IS 'Code pays ISO 3166-1 alpha-2 (FR, BE, CH, etc.)';
COMMENT ON COLUMN public.users.language IS 'Code langue ISO 639-1 (fr, en, etc.)';

-- 4. Mettre à jour les utilisateurs existants (optionnel)
UPDATE public.users
SET
    account_type = 'individual',
    country = 'FR',
    language = 'fr'
WHERE account_type IS NULL;
```

**Commande pour exécuter:**
```bash
psql -U stoflow_user -d stoflow_db -f /home/maribeiro/Stoflow/Stoflow_BackEnd/migrations/add_onboarding_fields.sql
```

---

### 3. Store Auth Frontend

**Fichier:** `/home/maribeiro/Stoflow/Stoflow_FrontEnd/stores/auth.ts`

**Interface User à mettre à jour:**

```typescript
interface User {
  id: number
  email: string
  full_name: string
  role: 'user' | 'admin'
  subscription_tier: 'starter' | 'standard' | 'premium' | 'business' | 'enterprise'

  // Onboarding fields (Added: 2024-12-08)
  business_name?: string
  account_type: 'individual' | 'professional'
  business_type?: 'resale' | 'dropshipping' | 'artisan' | 'retail' | 'other'
  estimated_products?: '0-50' | '50-200' | '200-500' | '500+'

  // Professional fields
  siret?: string
  vat_number?: string

  // Contact
  phone?: string
  country: string
  language: string
}

interface RegisterData {
  email: string
  password: string
  full_name: string
  business_name?: string
  account_type?: 'individual' | 'professional'
  business_type?: string
  estimated_products?: string
  siret?: string
  vat_number?: string
  phone?: string
  country?: string
  language?: string
}
```

**Méthode register à mettre à jour:**

```typescript
async register(data: RegisterData) {
  this.isLoading = true
  this.error = null

  try {
    const config = useRuntimeConfig()
    const baseURL = config.public.apiUrl

    const response = await fetch(`${baseURL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        business_name: data.business_name,
        account_type: data.account_type || 'individual',
        business_type: data.business_type,
        estimated_products: data.estimated_products,
        siret: data.siret,
        vat_number: data.vat_number,
        phone: data.phone,
        country: data.country || 'FR',
        language: data.language || 'fr'
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Erreur lors de l\'inscription')
    }

    const authData: AuthResponse = await response.json()

    // Créer l'objet User depuis la réponse
    const user: User = {
      id: authData.user_id,
      email: data.email,
      full_name: data.full_name,
      role: authData.role as 'user' | 'admin',
      subscription_tier: authData.subscription_tier as User['subscription_tier'],
      business_name: data.business_name,
      account_type: data.account_type || 'individual',
      business_type: data.business_type,
      estimated_products: data.estimated_products,
      siret: data.siret,
      vat_number: data.vat_number,
      phone: data.phone,
      country: data.country || 'FR',
      language: data.language || 'fr'
    }

    // Stocker dans le state et localStorage
    this.user = user
    this.token = authData.access_token
    this.refreshToken = authData.refresh_token
    this.isAuthenticated = true

    if (process.client) {
      localStorage.setItem('token', authData.access_token)
      localStorage.setItem('refresh_token', authData.refresh_token)
      localStorage.setItem('user', JSON.stringify(user))
    }

    return { success: true }
  } catch (error: any) {
    this.error = error.message || 'Erreur lors de l\'inscription'
    throw error
  } finally {
    this.isLoading = false
  }
}
```

---

### 4. Formulaire d'Inscription Frontend

**Fichier à créer:** `/home/maribeiro/Stoflow/Stoflow_FrontEnd/pages/register-enhanced.vue`

```vue
<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-8">
    <Card class="w-full max-w-2xl shadow-xl border border-gray-100">
      <template #title>
        <div class="flex items-center gap-3 bg-primary-400 -mx-6 -mt-6 px-6 py-5">
          <i class="pi pi-user-plus text-secondary-900 text-3xl"></i>
          <div>
            <h2 class="text-secondary-900 font-bold text-2xl">Créer un compte</h2>
            <p class="text-secondary-800 text-sm font-normal">Rejoignez Stoflow en quelques instants</p>
          </div>
        </div>
      </template>

      <template #content>
        <form @submit.prevent="handleRegister" class="space-y-6">

          <!-- Toggle Particulier / Professionnel -->
          <div class="bg-secondary-50 rounded-xl p-4 border-2 border-primary-200">
            <label class="block text-sm font-bold text-secondary-900 mb-3">
              Type de compte *
            </label>
            <div class="flex gap-4">
              <div
                class="flex-1 cursor-pointer"
                @click="form.account_type = 'individual'"
              >
                <div
                  class="p-4 rounded-lg border-2 transition-all"
                  :class="form.account_type === 'individual'
                    ? 'border-primary-400 bg-primary-100'
                    : 'border-gray-200 bg-white hover:border-primary-200'"
                >
                  <div class="flex items-center gap-3">
                    <RadioButton
                      v-model="form.account_type"
                      value="individual"
                      input-id="individual"
                    />
                    <label for="individual" class="cursor-pointer flex-1">
                      <div class="font-bold text-secondary-900">Particulier</div>
                      <div class="text-xs text-gray-600">Pour la revente occasionnelle</div>
                    </label>
                  </div>
                </div>
              </div>

              <div
                class="flex-1 cursor-pointer"
                @click="form.account_type = 'professional'"
              >
                <div
                  class="p-4 rounded-lg border-2 transition-all"
                  :class="form.account_type === 'professional'
                    ? 'border-primary-400 bg-primary-100'
                    : 'border-gray-200 bg-white hover:border-primary-200'"
                >
                  <div class="flex items-center gap-3">
                    <RadioButton
                      v-model="form.account_type"
                      value="professional"
                      input-id="professional"
                    />
                    <label for="professional" class="cursor-pointer flex-1">
                      <div class="font-bold text-secondary-900">Professionnel</div>
                      <div class="text-xs text-gray-600">Entreprise ou auto-entrepreneur</div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Informations de base -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="full_name" class="block text-sm font-bold text-secondary-900 mb-2">
                Nom complet *
              </label>
              <InputText
                id="full_name"
                v-model="form.full_name"
                placeholder="Jean Dupont"
                class="w-full"
                :invalid="!!errors.full_name"
                required
              />
              <small v-if="errors.full_name" class="text-red-500">{{ errors.full_name }}</small>
            </div>

            <div>
              <label for="business_name" class="block text-sm font-bold text-secondary-900 mb-2">
                {{ form.account_type === 'professional' ? 'Nom de l\'entreprise *' : 'Nom de la boutique' }}
              </label>
              <InputText
                id="business_name"
                v-model="form.business_name"
                :placeholder="form.account_type === 'professional' ? 'Dupont SARL' : 'Ma Boutique'"
                class="w-full"
                :invalid="!!errors.business_name"
                :required="form.account_type === 'professional'"
              />
              <small v-if="errors.business_name" class="text-red-500">{{ errors.business_name }}</small>
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-bold text-secondary-900 mb-2">
              Email *
            </label>
            <InputText
              id="email"
              v-model="form.email"
              type="email"
              placeholder="votre@email.com"
              class="w-full"
              :invalid="!!errors.email"
              required
            />
            <small v-if="errors.email" class="text-red-500">{{ errors.email }}</small>
          </div>

          <div>
            <label for="password" class="block text-sm font-bold text-secondary-900 mb-2">
              Mot de passe *
            </label>
            <Password
              id="password"
              v-model="form.password"
              placeholder="••••••••••••"
              class="w-full"
              :feedback="true"
              toggleMask
              :invalid="!!errors.password"
              required
              promptLabel="Entrez un mot de passe"
              weakLabel="Faible"
              mediumLabel="Moyen"
              strongLabel="Fort"
            >
              <template #footer>
                <Divider />
                <p class="text-xs text-gray-600 mt-2 font-bold">Exigences :</p>
                <ul class="text-xs text-gray-600 ml-4 mt-1 space-y-1">
                  <li>✓ Au moins 12 caractères</li>
                  <li>✓ 1 majuscule, 1 minuscule, 1 chiffre</li>
                  <li>✓ 1 caractère spécial (!@#$%^&*)</li>
                </ul>
              </template>
            </Password>
            <small v-if="errors.password" class="text-red-500">{{ errors.password }}</small>
          </div>

          <!-- Informations business -->
          <Divider />

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="business_type" class="block text-sm font-bold text-secondary-900 mb-2">
                Type d'activité
              </label>
              <Dropdown
                id="business_type"
                v-model="form.business_type"
                :options="businessTypes"
                optionLabel="label"
                optionValue="value"
                placeholder="Sélectionnez votre activité"
                class="w-full"
              />
            </div>

            <div>
              <label for="estimated_products" class="block text-sm font-bold text-secondary-900 mb-2">
                Nombre de produits estimé
              </label>
              <Dropdown
                id="estimated_products"
                v-model="form.estimated_products"
                :options="productRanges"
                optionLabel="label"
                optionValue="value"
                placeholder="Combien de produits ?"
                class="w-full"
              />
            </div>
          </div>

          <!-- Champs professionnels (conditionnels) -->
          <div v-if="form.account_type === 'professional'" class="space-y-4 bg-blue-50 rounded-xl p-4 border border-blue-200">
            <div class="flex items-center gap-2 mb-3">
              <i class="pi pi-building text-blue-600"></i>
              <span class="font-bold text-blue-900">Informations professionnelles</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label for="siret" class="block text-sm font-bold text-secondary-900 mb-2">
                  Numéro SIRET
                </label>
                <InputText
                  id="siret"
                  v-model="form.siret"
                  placeholder="12345678901234"
                  class="w-full"
                  :invalid="!!errors.siret"
                  maxlength="14"
                />
                <small v-if="errors.siret" class="text-red-500">{{ errors.siret }}</small>
                <small class="text-gray-600">14 chiffres (France)</small>
              </div>

              <div>
                <label for="vat_number" class="block text-sm font-bold text-secondary-900 mb-2">
                  Numéro de TVA
                </label>
                <InputText
                  id="vat_number"
                  v-model="form.vat_number"
                  placeholder="FR12345678901"
                  class="w-full"
                  :invalid="!!errors.vat_number"
                />
                <small v-if="errors.vat_number" class="text-red-500">{{ errors.vat_number }}</small>
              </div>
            </div>
          </div>

          <!-- Contact -->
          <div>
            <label for="phone" class="block text-sm font-bold text-secondary-900 mb-2">
              Téléphone (optionnel)
            </label>
            <InputText
              id="phone"
              v-model="form.phone"
              type="tel"
              placeholder="+33 6 12 34 56 78"
              class="w-full"
            />
          </div>

          <!-- Message d'erreur global -->
          <div v-if="authStore.error" class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div class="flex items-center gap-2">
              <i class="pi pi-exclamation-triangle text-red-600"></i>
              <p class="text-red-700 text-sm font-bold">
                {{ authStore.error }}
              </p>
            </div>
          </div>

          <!-- Bouton submit -->
          <Button
            type="submit"
            label="Créer mon compte"
            icon="pi pi-check"
            class="w-full bg-secondary-900 hover:bg-secondary-800 border-0 font-bold text-lg py-3"
            :loading="authStore.isLoading"
          />
        </form>
      </template>

      <template #footer>
        <div class="text-center text-sm text-secondary-900 border-t-2 border-primary-400 pt-4">
          Déjà un compte ?
          <NuxtLink to="/login" class="text-primary-600 hover:text-primary-700 underline font-bold">
            Se connecter
          </NuxtLink>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { useToast } from 'primevue/usetoast'

const authStore = useAuthStore()
const router = useRouter()
const toast = useToast()

// Formulaire
const form = reactive({
  account_type: 'individual' as 'individual' | 'professional',
  full_name: '',
  business_name: '',
  email: '',
  password: '',
  business_type: null as string | null,
  estimated_products: null as string | null,
  siret: '',
  vat_number: '',
  phone: '',
  country: 'FR',
  language: 'fr'
})

// Erreurs
const errors = reactive({
  full_name: '',
  business_name: '',
  email: '',
  password: '',
  siret: '',
  vat_number: ''
})

// Options
const businessTypes = [
  { label: 'Revente', value: 'resale' },
  { label: 'Dropshipping', value: 'dropshipping' },
  { label: 'Artisanat', value: 'artisan' },
  { label: 'Commerce de détail', value: 'retail' },
  { label: 'Autre', value: 'other' }
]

const productRanges = [
  { label: '0 à 50 produits', value: '0-50' },
  { label: '50 à 200 produits', value: '50-200' },
  { label: '200 à 500 produits', value: '200-500' },
  { label: 'Plus de 500 produits', value: '500+' }
]

// Validation
const validateForm = (): boolean => {
  let isValid = true

  // Reset errors
  Object.keys(errors).forEach(key => errors[key] = '')

  // Full name
  if (!form.full_name || form.full_name.trim().length === 0) {
    errors.full_name = 'Nom complet requis'
    isValid = false
  }

  // Business name (requis si professional)
  if (form.account_type === 'professional' && (!form.business_name || form.business_name.trim().length === 0)) {
    errors.business_name = 'Nom de l\'entreprise requis'
    isValid = false
  }

  // Email
  if (!form.email) {
    errors.email = 'Email requis'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Email invalide'
    isValid = false
  }

  // Password
  if (!form.password) {
    errors.password = 'Mot de passe requis'
    isValid = false
  } else if (form.password.length < 12) {
    errors.password = 'Minimum 12 caractères'
    isValid = false
  } else {
    const hasUppercase = /[A-Z]/.test(form.password)
    const hasLowercase = /[a-z]/.test(form.password)
    const hasNumber = /[0-9]/.test(form.password)
    const hasSpecial = /[!@#$%^&*]/.test(form.password)

    if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecial) {
      errors.password = 'Doit contenir: 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial'
      isValid = false
    }
  }

  // SIRET (si professionnel et rempli)
  if (form.account_type === 'professional' && form.siret) {
    const siretClean = form.siret.replace(/\s/g, '')
    if (!/^\d{14}$/.test(siretClean)) {
      errors.siret = 'SIRET doit contenir exactement 14 chiffres'
      isValid = false
    }
  }

  return isValid
}

// Submit
const handleRegister = async () => {
  if (!validateForm()) return

  try {
    await authStore.register({
      email: form.email,
      password: form.password,
      full_name: form.full_name,
      business_name: form.business_name || undefined,
      account_type: form.account_type,
      business_type: form.business_type || undefined,
      estimated_products: form.estimated_products || undefined,
      siret: form.siret || undefined,
      vat_number: form.vat_number || undefined,
      phone: form.phone || undefined,
      country: form.country,
      language: form.language
    })

    toast.add({
      severity: 'success',
      summary: 'Compte créé',
      detail: `Bienvenue sur Stoflow, ${form.full_name} !`,
      life: 3000
    })

    router.push('/dashboard')
  } catch (error: any) {
    toast.add({
      severity: 'error',
      summary: 'Erreur d\'inscription',
      detail: error.message || 'Impossible de créer le compte',
      life: 5000
    })
  }
}

// Rediriger si déjà connecté
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
:deep(.p-password input) {
  width: 100%;
}
</style>
```

---

## 🚀 Marche à suivre pour finaliser

### 1. Modifier l'endpoint register (Backend)
```bash
# Ouvrir le fichier
nano /home/maribeiro/Stoflow/Stoflow_BackEnd/api/auth.py

# Ajouter les imports en haut du fichier
from models.public.user import AccountType, BusinessType, EstimatedProducts

# Modifier la création du User (voir section ci-dessus)
```

### 2. Exécuter la migration SQL
```bash
# Créer le fichier de migration
nano /home/maribeiro/Stoflow/Stoflow_BackEnd/migrations/add_onboarding_fields.sql

# Copier le contenu SQL ci-dessus

# Exécuter la migration
psql -U stoflow_user -d stoflow_db -f /home/maribeiro/Stoflow/Stoflow_BackEnd/migrations/add_onboarding_fields.sql
```

### 3. Modifier le store auth (Frontend)
```bash
# Le fichier est déjà créé, il faut juste modifier la méthode register
# Voir section ci-dessus
```

### 4. Créer le nouveau formulaire (Frontend)
```bash
# Créer le fichier
# Le code complet est fourni ci-dessus dans register-enhanced.vue
```

### 5. Tester
```bash
# Frontend
cd /home/maribeiro/Stoflow/Stoflow_FrontEnd
npm run dev

# Backend
cd /home/maribeiro/Stoflow/Stoflow_BackEnd
# Lancer le serveur FastAPI

# Accéder à http://localhost:3000/register-enhanced
```

---

## 📝 Notes importantes

1. **Migration SQL** : À exécuter UNE SEULE FOIS sur la base de données
2. **Ancien formulaire** : Le fichier `register.vue` existant reste inchangé pour compatibilité
3. **Nouveau formulaire** : `register-enhanced.vue` est le nouveau formulaire complet
4. **Types ENUMs** : Bien vérifier que PostgreSQL crée les ENUMs avant d'ajouter les colonnes

---

## ✅ Checklist finale

- [ ] Modifier endpoint /register (Backend)
- [ ] Créer et exécuter migration SQL
- [ ] Mettre à jour store auth (Frontend)
- [ ] Créer register-enhanced.vue (Frontend)
- [ ] Tester inscription Particulier
- [ ] Tester inscription Professionnel avec SIRET
- [ ] Vérifier que les données sont bien enregistrées en base
- [ ] Tester le login après inscription

---

**Dernière mise à jour:** 2024-12-08
**Auteur:** Claude Code Assistant
