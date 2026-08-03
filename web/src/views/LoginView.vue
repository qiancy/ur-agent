<script setup lang="ts">
import { ref } from 'vue'
import { sellerLogin, type SellerLoginResult } from '../api/seller'
import { registerAccount } from '../api/auth'

const emit = defineEmits<{
  (e: 'authenticated', result: SellerLoginResult): void
}>()

const mode = ref<'login' | 'register'>('login')
const login = ref('')
const password = ref('')
const name = ref('')
const puid = ref('')
const initialOuid = ref('')
const error = ref('')
const noSpace = ref('')
const loading = ref(false)

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
  noSpace.value = ''
}

async function onSubmit() {
  error.value = ''
  noSpace.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      const result = await sellerLogin(login.value.trim(), password.value)
      emit('authenticated', result)
    } else {
      const result = await registerAccount({
        login: login.value.trim(),
        password: password.value,
        name: name.value.trim(),
        puid: puid.value.trim() || undefined,
        initialOuid: initialOuid.value.trim() || undefined,
      })
      if (result.requires_organization || !result.access_token) {
        noSpace.value = '注册成功，暂无业务空间。请联系管理员将你加入一个空间后再登录。'
        return
      }
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
  <div class="login-card">
    <h1 class="login-title">Uni-Resource Agent</h1>
    <p class="login-subtitle">一个账号，多个空间</p>
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
        <label class="field">
          <span class="field-label">初始空间 ouid（可选）</span>
          <input
            v-model="initialOuid"
            data-test="register-initial-ouid"
            type="text"
            placeholder="不填则注册后暂无空间"
          />
        </label>
      </template>
      <p v-if="error" class="form-error" data-test="login-error">{{ error }}</p>
      <p v-if="noSpace" class="form-notice" data-test="no-space">{{ noSpace }}</p>
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
</template>

<style scoped>
.login-card {
  width: 360px;
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
.form-notice {
  margin: 0;
  font-size: 13px;
  color: var(--amber, #9a6700);
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
.switch-line {
  margin: 14px 0 0;
  text-align: center;
}
.link-btn {
  border: none;
  background: none;
  padding: 4px;
  font-size: 13px;
  color: var(--blue, #1d4f91);
  cursor: pointer;
}
</style>
