<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuth } from '../composables/useAuth';
import LoginForm from '../components/LoginForm.vue';
import DevModeBanner from '../components/DevModeBanner.vue';
import VintedSessionInfo from '../components/VintedSessionInfo.vue';
import {
  getEnvironmentMode,
  setEnvironmentMode,
  type EnvironmentMode
} from '../config/environment';

const { isAuthenticated, user, checkAuth } = useAuth();

const environmentMode = ref<EnvironmentMode>('localhost');

onMounted(async () => {
  await checkAuth();
  environmentMode.value = await getEnvironmentMode();
});

const toggleEnvironment = async () => {
  const newMode: EnvironmentMode = environmentMode.value === 'localhost' ? 'production' : 'localhost';
  environmentMode.value = newMode;
  await setEnvironmentMode(newMode);
};
</script>

<template>
  <div class="popup-container">
    <DevModeBanner />

    <header>
      <h1>Stoflow Plugin</h1>
    </header>

    <main>
      <!-- Formulaire de connexion si non authentifié -->
      <LoginForm v-if="!isAuthenticated" />

      <!-- Statut si authentifié -->
      <div v-else class="status-container">
        <!-- Connexion Stoflow -->
        <div class="status-card">
          <div class="status-header">
            <div class="status-icon connected">🟢</div>
            <div>
              <h2>Connexion Stoflow</h2>
              <p class="status-detail">Authentifié</p>
            </div>
          </div>
          <div class="user-info">
            <span class="user-email">{{ user?.email || 'Utilisateur' }}</span>
          </div>
        </div>

        <!-- Connexion Vinted avec informations détaillées -->
        <VintedSessionInfo />

        <!-- Info automatique -->
        <div class="info-card">
          <p class="info-text">
            ℹ️ La synchronisation se fait <strong>automatiquement</strong> en arrière-plan.
          </p>
        </div>
      </div>
    </main>

    <!-- Environment Toggle Footer -->
    <footer class="environment-footer">
      <div class="env-toggle" @click="toggleEnvironment">
        <span class="env-label">Backend:</span>
        <div class="env-switch" :class="{ production: environmentMode === 'production' }">
          <span class="env-option" :class="{ active: environmentMode === 'localhost' }">Local</span>
          <span class="env-option" :class="{ active: environmentMode === 'production' }">Prod</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.popup-container {
  width: 380px;
  min-height: 400px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f9fafb;
}

header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #111827;
}

main {
  padding: 16px;
}

.status-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.status-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.status-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f3f4f6;
}

.status-icon.connected {
  background: #dcfce7;
}

.status-icon.disconnected {
  background: #fee2e2;
}

h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #111827;
}

.status-detail {
  font-size: 13px;
  color: #6b7280;
  margin: 2px 0 0;
}

.user-info {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.user-email {
  font-size: 14px;
  color: #4b5563;
  font-weight: 500;
}

.info-card {
  background: #eff6ff;
  border-radius: 8px;
  padding: 12px;
  border-left: 3px solid #3b82f6;
}

.info-text {
  margin: 0;
  font-size: 13px;
  color: #1e40af;
  line-height: 1.5;
}

/* Environment Toggle Footer */
.environment-footer {
  position: sticky;
  bottom: 0;
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 12px 16px;
}

.env-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
}

.env-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.env-switch {
  display: flex;
  background: #f3f4f6;
  border-radius: 6px;
  padding: 2px;
  transition: background 0.2s;
}

.env-option {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  border-radius: 4px;
  transition: all 0.2s;
}

.env-option.active {
  background: white;
  color: #111827;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.env-switch.production .env-option.active {
  background: #3b82f6;
  color: white;
}
</style>
