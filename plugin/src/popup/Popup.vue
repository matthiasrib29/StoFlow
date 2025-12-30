<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuth } from '../composables/useAuth';
import LoginForm from '../components/LoginForm.vue';
import DevModeBanner from '../components/DevModeBanner.vue';
import VintedSessionInfo from '../components/VintedSessionInfo.vue';

const { isAuthenticated, user, checkAuth } = useAuth();

onMounted(async () => {
  await checkAuth();
});
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
</style>
