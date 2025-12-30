<script setup lang="ts">
import { ref, onMounted } from 'vue';

interface Settings {
  syncInterval: number;
  autoSync: boolean;
  notifications: boolean;
  platforms: {
    vinted: { enabled: boolean; autoImport: boolean };
    ebay: { enabled: boolean; autoImport: boolean };
    etsy: { enabled: boolean; autoImport: boolean };
  };
}

const settings = ref<Settings>({
  syncInterval: 60,
  autoSync: true,
  notifications: true,
  platforms: {
    vinted: { enabled: true, autoImport: false },
    ebay: { enabled: true, autoImport: false },
    etsy: { enabled: false, autoImport: false }
  }
});

const saving = ref(false);
const saveMessage = ref('');

onMounted(async () => {
  const stored = await chrome.storage.local.get('settings');
  if (stored.settings) {
    settings.value = stored.settings;
  }
});

const saveSettings = async () => {
  saving.value = true;
  saveMessage.value = '';

  try {
    await chrome.storage.local.set({ settings: settings.value });

    // Mettre à jour l'intervalle de sync
    await chrome.runtime.sendMessage({
      action: 'UPDATE_SYNC_INTERVAL',
      interval: settings.value.syncInterval / 60 // Convertir secondes en minutes
    });

    saveMessage.value = '✅ Paramètres enregistrés !';
  } catch (error) {
    saveMessage.value = "❌ Erreur lors de l'enregistrement";
  } finally {
    saving.value = false;
    setTimeout(() => (saveMessage.value = ''), 3000);
  }
};
</script>

<template>
  <div class="options-page">
    <header>
      <h1>⚙️ Paramètres Stoflow Plugin</h1>
    </header>

    <main>
      <section class="settings-section">
        <h2>🔄 Synchronisation</h2>
        <div class="setting-item">
          <label class="checkbox-label">
            <input v-model="settings.autoSync" type="checkbox" />
            <span>Synchronisation automatique des ventes</span>
          </label>
          <p class="help-text">
            Vérifie automatiquement les nouvelles ventes sur toutes les plateformes
          </p>
        </div>

        <div class="setting-item">
          <label>
            <span class="label-text">Intervalle de synchronisation</span>
            <select v-model.number="settings.syncInterval" class="select-input">
              <option :value="30">30 secondes</option>
              <option :value="60">1 minute (recommandé)</option>
              <option :value="300">5 minutes</option>
              <option :value="900">15 minutes</option>
            </select>
          </label>
          <p class="help-text">Temps entre chaque vérification des ventes</p>
        </div>
      </section>

      <section class="settings-section">
        <h2>🔔 Notifications</h2>
        <div class="setting-item">
          <label class="checkbox-label">
            <input v-model="settings.notifications" type="checkbox" />
            <span>Afficher notifications lors des ventes</span>
          </label>
          <p class="help-text">
            Recevoir une notification desktop quand un produit est vendu
          </p>
        </div>
      </section>

      <section class="settings-section">
        <h2>🌐 Plateformes</h2>

        <div
          v-for="(config, name) in settings.platforms"
          :key="name"
          class="platform-setting"
        >
          <div class="platform-header">
            <h3>{{ name.charAt(0).toUpperCase() + name.slice(1) }}</h3>
          </div>

          <div class="setting-item">
            <label class="checkbox-label">
              <input v-model="config.enabled" type="checkbox" />
              <span>Activer {{ name }}</span>
            </label>
          </div>

          <div v-if="config.enabled" class="setting-item">
            <label class="checkbox-label">
              <input v-model="config.autoImport" type="checkbox" />
              <span>Import automatique au démarrage</span>
            </label>
          </div>
        </div>
      </section>

      <div class="actions">
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="saveSettings"
        >
          {{ saving ? 'Enregistrement...' : 'Enregistrer les paramètres' }}
        </button>

        <div
          v-if="saveMessage"
          class="save-message"
          :class="{ error: saveMessage.includes('❌') }"
        >
          {{ saveMessage }}
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.options-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 32px;
  color: #111827;
}

.settings-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.settings-section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #374151;
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type='checkbox'] {
  width: 20px;
  height: 20px;
  margin-right: 12px;
  cursor: pointer;
}

.checkbox-label span {
  font-size: 14px;
  color: #374151;
}

.label-text {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #374151;
}

.select-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.help-text {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.platform-setting {
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.platform-setting:last-child {
  margin-bottom: 0;
}

.platform-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #111827;
}

.actions {
  margin-top: 32px;
  text-align: center;
}

.btn {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-message {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  background: #dcfce7;
  color: #166534;
}

.save-message.error {
  background: #fee2e2;
  color: #991b1b;
}
</style>
