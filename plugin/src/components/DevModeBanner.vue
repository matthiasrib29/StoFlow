<script setup lang="ts">
import { ref, onMounted } from 'vue';

const devMode = ref(false);
const devEmail = ref('');

onMounted(async () => {
  const result = await chrome.storage.local.get(['dev_mode', 'dev_email']);
  devMode.value = result.dev_mode || false;
  devEmail.value = result.dev_email || '';
});
</script>

<template>
  <div v-if="devMode" class="dev-banner">
    🔧 MODE DÉVELOPPEMENT - Email: {{ devEmail }}
  </div>
</template>

<style scoped>
.dev-banner {
  background: #fef3c7;
  color: #92400e;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  border-bottom: 2px solid #fbbf24;
}
</style>
