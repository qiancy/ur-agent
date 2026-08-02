<script setup lang="ts">
import { ref } from 'vue'
import { sellerLogin, type SellerLoginResult } from '../api/seller'

const emit = defineEmits<{
  (e: 'authenticated', result: SellerLoginResult): void
}>()

const login = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const result = await sellerLogin(login.value.trim(), password.value)
    emit('authenticated', result)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-card">
    <h1 class="login-title">Uni-Resource Agent</h1>
    <p class="login-subtitle">店铺工作台</p>
    <form class="login-form" data-test="login-form" @submit.prevent="onSubmit">
      <label class="field">
        <span class="field-label">登录账号</span>
        <input
          v-model="login"
          data-test="login"
          type="text"
          placeholder="puid@ouid"
          autocomplete="username"
        />
      </label>
      <label class="field">
        <span class="field-label">密码</span>
        <input
          v-model="password"
          data-test="password"
          type="password"
          placeholder="••••••••"
          autocomplete="current-password"
        />
      </label>
      <p v-if="error" class="form-error" data-test="login-error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? '登录中…' : '登录' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login-card {
  width: 340px;
  margin: 0 auto;
  padding: 32px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(23, 32, 42, 0.06);
}
.login-title {
  margin: 0;
  font-size: 20px;
  color: var(--ink, #17202a);
}
.login-subtitle {
  margin: 4px 0 20px;
  color: var(--muted, #637083);
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 13px;
  color: var(--muted, #637083);
}
input {
  padding: 9px 11px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  font-size: 14px;
}
input:focus {
  outline: 2px solid var(--blue, #1d4f91);
  outline-offset: 1px;
}
.form-error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
.btn {
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}
.btn-primary {
  background: var(--blue, #1d4f91);
  color: #fff;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
