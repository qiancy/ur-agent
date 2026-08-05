<script setup lang="ts">
import { ref } from 'vue'
import { loginAccount, registerAccount } from '../api/auth'
import type { SellerLoginResult } from '../api/seller'

const emit = defineEmits<{
  (e: 'authenticated', result: SellerLoginResult): void
}>()

const mode = ref<'login' | 'register'>('login')
const login = ref('')
const password = ref('')
const name = ref('')
const puid = ref('')
const error = ref('')
const loading = ref(false)

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      const result = await loginAccount(login.value.trim(), password.value)
      emit('authenticated', result)
    } else {
      const result = await registerAccount({
        login: login.value.trim(),
        password: password.value,
        name: name.value.trim(),
        puid: puid.value.trim() || undefined,
      })
      emit('authenticated', result)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="brand">
        <div class="mark">UA</div>
        <div>
          <h1 class="login-title">Uni-Resource Agent</h1>
          <p class="login-subtitle">一个账号，多个空间</p>
        </div>
      </div>
      <form class="login-form" data-test="login-form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field-label">登录账号</span>
          <input
            v-model="login"
            data-test="login"
            type="text"
            placeholder="zhansan"
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
        <template v-if="mode === 'register'">
          <label class="field">
            <span class="field-label">姓名</span>
            <input v-model="name" data-test="register-name" type="text" placeholder="张三" />
          </label>
          <label class="field">
            <span class="field-label">puid（可选）</span>
            <input
              v-model="puid"
              data-test="register-puid"
              type="text"
              placeholder="不填则默认取账号"
            />
          </label>
        </template>
        <p v-if="error" class="form-error" data-test="login-error">{{ error }}</p>
        <button class="btn btn-primary" type="submit" :disabled="loading">
          {{ loading ? '处理中…' : mode === 'login' ? '登录' : '注册' }}
        </button>
      </form>
      <p class="switch-line">
        <button
          v-if="mode === 'login'"
          class="link-btn"
          data-test="go-register"
          type="button"
          @click="switchMode('register')"
        >
          注册新账号
        </button>
        <button
          v-else
          class="link-btn"
          data-test="go-login"
          type="button"
          @click="switchMode('login')"
        >
          返回登录
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg, #f8fafc);
}
.login-card {
  width: 100%;
  max-width: 400px;
  padding: 32px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(23, 32, 42, 0.06);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.mark {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #243447;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 15px;
  flex-shrink: 0;
}
.login-title {
  margin: 0;
  font-size: 20px;
  font-weight: 750;
  color: var(--ink, #17202a);
  line-height: 1.3;
}
.login-subtitle {
  margin: 4px 0 0;
  color: var(--muted, #637083);
  font-size: 13px;
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
  padding: 10px 12px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  font-size: 14px;
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
}
input:focus {
  outline: 2px solid var(--teal, #0f766e);
  outline-offset: 1px;
}
.form-error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #ef4444);
}
.btn {
  padding: 11px 14px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 650;
  cursor: pointer;
}
.btn-primary {
  background: var(--teal, #0f766e);
  color: #fff;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: default;
}
.switch-line {
  margin: 14px 0 0;
  text-align: center;
}
.link-btn {
  border: none;
  background: none;
  padding: 4px;
  font-size: 13px;
  color: var(--teal, #0f766e);
  cursor: pointer;
}
.link-btn:hover {
  text-decoration: underline;
}
</style>
