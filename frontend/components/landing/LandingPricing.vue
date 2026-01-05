<template>
  <section id="pricing" class="py-20 lg:py-32 bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12 animate-on-scroll">
        <span class="inline-block text-sm font-semibold text-secondary-700 uppercase tracking-wider mb-3">Tarification</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Tarifs simples et transparents
        </h2>
        <p class="text-xl text-secondary-700 max-w-2xl mx-auto">
          Pas de frais cachés. Annulez à tout moment.
        </p>
      </div>

      <!-- Billing Toggle -->
      <div class="flex justify-center mb-12">
        <div class="inline-flex items-center bg-white rounded-full p-1 border-2 border-gray-200 shadow-sm">
          <button
            :class="[
              'px-6 py-2 rounded-full text-sm font-semibold transition-all',
              !isYearly ? 'bg-secondary-900 text-white' : 'text-secondary-600 hover:text-secondary-900'
            ]"
            @click="isYearly = false"
          >
            Mensuel
          </button>
          <button
            :class="[
              'px-6 py-2 rounded-full text-sm font-semibold transition-all flex items-center gap-2',
              isYearly ? 'bg-secondary-900 text-white' : 'text-secondary-600 hover:text-secondary-900'
            ]"
            @click="isYearly = true"
          >
            Annuel
            <span class="bg-primary-400 text-secondary-900 text-xs font-bold px-2 py-0.5 rounded-full">
              -20%
            </span>
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="flex justify-center py-12">
        <i class="pi pi-spin pi-spinner text-4xl text-secondary-400" />
      </div>

      <!-- Pricing cards -->
      <div v-else class="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
        <div
          v-for="plan in plans"
          :key="plan.tier"
          :class="[
            'rounded-2xl p-8 border-2 animate-on-scroll transition-all duration-300',
            plan.is_popular
              ? 'bg-secondary-900 border-primary-400 shadow-xl transform lg:-translate-y-4'
              : 'bg-white border-gray-200 hover:border-secondary-300'
          ]"
        >
          <!-- Popular badge -->
          <div v-if="plan.is_popular" class="inline-block bg-primary-400 text-secondary-900 text-sm font-bold px-3 py-1 rounded-full mb-4">
            Populaire
          </div>

          <!-- Plan name -->
          <h3 :class="['text-xl font-bold mb-2', plan.is_popular ? 'text-white' : 'text-secondary-900']">
            {{ plan.display_name }}
          </h3>

          <!-- Description -->
          <p :class="['mb-6', plan.is_popular ? 'text-gray-400' : 'text-secondary-700']">
            {{ plan.description }}
          </p>

          <!-- Price -->
          <div class="mb-2">
            <span
              v-if="isYearly && plan.annual_discount_percent > 0"
              :class="['text-lg line-through mr-2', plan.is_popular ? 'text-gray-500' : 'text-gray-400']"
            >
              {{ plan.price }}€
            </span>
            <span :class="['text-4xl font-bold', plan.is_popular ? 'text-white' : 'text-secondary-900']">
              {{ isYearly && plan.annual_discount_percent > 0 ? getAnnualPrice(plan) : plan.price }}€
            </span>
            <span :class="[plan.is_popular ? 'text-gray-400' : 'text-secondary-700']">/mois</span>
          </div>

          <!-- Savings -->
          <p
            v-if="isYearly && plan.annual_discount_percent > 0"
            :class="['text-sm mb-6 font-medium', plan.is_popular ? 'text-primary-400' : 'text-primary-600']"
          >
            Économisez {{ getAnnualSavings(plan) }}€/an
          </p>
          <div v-else class="mb-6" />

          <!-- Features -->
          <ul class="space-y-3 mb-8">
            <li
              v-for="feature in plan.features"
              :key="feature.feature_text"
              :class="['flex items-center gap-2', plan.is_popular ? 'text-gray-300' : 'text-secondary-600']"
            >
              <i :class="['pi pi-check', plan.is_popular ? 'text-primary-400' : 'text-primary-500']" />
              <span>{{ feature.feature_text }}</span>
            </li>
          </ul>

          <!-- CTA Button -->
          <Button
            :label="plan.cta_text || 'Commencer'"
            :icon="plan.tier !== 'free' ? 'pi pi-arrow-right' : undefined"
            :icon-pos="plan.tier !== 'free' ? 'right' : undefined"
            :class="[
              'w-full font-bold',
              plan.is_popular
                ? 'bg-primary-400 hover:bg-primary-500 text-secondary-900 border-0'
                : 'bg-transparent text-secondary-900 border-2 border-secondary-900 hover:bg-secondary-900 hover:text-white'
            ]"
            @click="$emit('planClick', plan)"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { PricingPlan } from '~/composables/usePricing'

defineProps<{
  plans: PricingPlan[]
  loading: boolean
  getAnnualPrice: (plan: PricingPlan) => number
  getAnnualSavings: (plan: PricingPlan) => number
}>()

defineEmits<{
  planClick: [plan: PricingPlan]
}>()

const isYearly = ref(true)
</script>
