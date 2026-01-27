<template>
  <section id="faq" class="py-20 lg:py-32 bg-white">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-16 animate-on-scroll">
        <h2 class="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
          Questions fréquentes
        </h2>
        <p class="text-xl text-secondary-600">
          Vous avez des questions ? Nous avons les réponses.
        </p>
      </div>

      <div class="space-y-4">
        <div
          v-for="(faq, index) in faqs"
          :key="index"
          class="border-2 border-gray-200 rounded-xl overflow-hidden animate-on-scroll"
        >
          <button
            class="w-full flex items-center justify-between p-6 text-left bg-white hover:bg-gray-50 transition-colors gap-4"
            @click="toggleFaq(index)"
          >
            <div class="flex items-center gap-4">
              <div class="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <i :class="['pi', faq.icon, 'text-secondary-700']" />
              </div>
              <h3 class="font-bold text-secondary-900">{{ faq.question }}</h3>
            </div>
            <i
              :class="openFaq === index ? 'pi pi-minus' : 'pi pi-plus'"
              class="text-primary-500 flex-shrink-0"
            />
          </button>
          <div
            v-show="openFaq === index"
            class="px-6 pb-6 pl-20 text-secondary-600"
          >
            {{ faq.answer }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { landingFaqs } from '~/data/landing-faqs'

const faqs = landingFaqs

const openFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  openFaq.value = openFaq.value === index ? null : index
}
</script>
