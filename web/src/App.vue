<script setup lang="ts">
import { ref } from 'vue'
import { getToken, clearToken } from './api/client'
import type { SellerLoginResult } from './api/seller'
import LoginView from './views/LoginView.vue'
import SummaryView from './views/SummaryView.vue'

const authenticated = ref(getToken() !== null)
const organizationName = ref('')

function onAuthenticated(result: SellerLoginResult) {
  organizationName.value = result.organization.name
  authenticated.value = true
}

function onLoggedOut() {
  clearToken()
  authenticated.value = false
}
</script>

<template>
  <div class="shell">
    <header v-if="authenticated" class="topbar">
      <span class="topbar-brand">Uni-Resource Agent</span>
      <span class="topbar-org">{{ organizationName }}</span>
      <button class="btn btn-ghost" type="button" @click="onLoggedOut">
        退出登录
      </button>
    </header>
    <main class="main">
      <LoginView v-if="!authenticated" @authenticated="onAuthenticated" />
      <SummaryView v-else @logged-out="onLoggedOut" />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg, #f4f6f8);
  font-family: 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--panel, #ffffff);
  border-bottom: 1px solid var(--line, #d8dee8);
}
.topbar-brand {
  font-weight: 600;
  color: var(--ink, #17202a);
}
.topbar-org {
  color: var(--muted, #637083);
}
.btn {
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
}
.btn-ghost {
  margin-left: auto;
  background: transparent;
  border: 1px solid var(--line, #d8dee8);
  color: var(--muted, #637083);
}
.main {
  padding: 24px;
}
</style>
