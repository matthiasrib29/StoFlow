<script setup lang="ts">
import { ref } from 'vue';

const emit = defineEmits<{
  login: [credentials: { email: string; password: string }]
}>();

const email = ref('');
const password = ref('');

const handleSubmit = () => {
  emit('login', {
    email: email.value,
    password: password.value
  });
};
</script>

<template>
  <form @submit.prevent="handleSubmit" class="login-form">
    <h2>Connexion Stoflow</h2>

    <div class="form-group">
      <label for="email">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        placeholder="votre@email.com"
        required
      />
    </div>

    <div class="form-group">
      <label for="password">Mot de passe</label>
      <input
        id="password"
        v-model="password"
        type="password"
        placeholder="••••••••"
        required
      />
    </div>

    <button type="submit" class="btn btn-primary">
      Se connecter
    </button>
  </form>
</template>

<style scoped>
.login-form {
  padding: 20px;
}

h2 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: #374151;
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}
</style>
