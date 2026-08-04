<script setup lang="ts">
import { reactive, ref } from 'vue'
import { createSpace } from '../api/spaceGovernance'
import type { SellerLoginResult } from '../api/seller'

const props = defineProps<{
  ouid: string
  orgType: string
  role: string
  puid: string
  personName: string
  organizationName: string
}>()

const emit = defineEmits<{
  (e: 'context-updated', result: SellerLoginResult): void
  (e: 'navigate-space', action: string): void
}>()

const ORG_TYPE_OPTIONS = [
  { value: 'family', label: '家庭' },
  { value: 'ecommerce', label: '电商店铺' },
  { value: 'campaign', label: '活动项目' },
  { value: 'starship', label: '星际任务' },
  { value: 'company', label: '公司/组织' },
]

const loading = ref(false)
const error = ref('')
const form = reactive({
  name: '',
  org_type: 'family',
  ouid: '',
  description: '',
})

async function onSubmit() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = '请填写空间名称'
    return
  }
  if (form.ouid.trim() && !/^[a-zA-Z0-9_-]+$/.test(form.ouid.trim())) {
    error.value = 'OUID 只允许英文字母、数字、下划线和连字符'
    return
  }
  loading.value = true
  try {
    const result = await createSpace({
      name: form.name.trim(),
      org_type: form.org_type,
      ...(form.ouid.trim() ? { ouid: form.ouid.trim() } : {}),
      ...(form.description.trim() ? { description: form.description.trim() } : {}),
    })
    emit('context-updated', result)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="space-create-view" data-test="space-create-view">
    <div class="head">
      <h2 class="title">创建空间</h2>
      <button
        type="button"
        class="btn"
        data-test="back-to-manage"
        @click="emit('navigate-space', 'manage')"
      >
        返回管理
      </button>
    </div>
    <form class="card" @submit.prevent="onSubmit">
      <label class="field">
        <span class="field-label">空间名称 *</span>
        <input
          v-model="form.name"
          data-test="create-name"
          type="text"
          placeholder="例如 家庭账本 / 我的小店"
          autocomplete="off"
        />
      </label>
      <label class="field">
        <span class="field-label">空间类型 *</span>
        <select v-model="form.org_type" class="select" data-test="create-org-type">
          <option v-for="opt in ORG_TYPE_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}（{{ opt.value }}）
          </option>
        </select>
      </label>
      <label class="field">
        <span class="field-label">OUID（可选，英文字母/数字/下划线/连字符）</span>
        <input
          v-model="form.ouid"
          data-test="create-ouid"
          type="text"
          placeholder="留空将自动生成"
          autocomplete="off"
        />
      </label>
      <label class="field">
        <span class="field-label">描述（可选）</span>
        <input
          v-model="form.description"
          data-test="create-description"
          type="text"
          placeholder="一句话描述这个空间"
          autocomplete="off"
        />
      </label>
      <p v-if="error" class="error" data-test="create-error">{{ error }}</p>
      <div class="actions">
        <button type="submit" class="btn primary" :disabled="loading" data-test="create-submit">
          {{ loading ? '创建中…' : '创建空间' }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.space-create-view {
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}
.card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 12px;
  color: var(--muted, #637083);
}
input,
.select {
  padding: 10px 12px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  font-size: 13px;
  background: #ffffff;
  color: var(--ink, #17202a);
}
input:focus {
  outline: 2px solid var(--blue, #1d4f91);
  outline-offset: 1px;
}
.error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
.actions {
  display: flex;
  justify-content: flex-end;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 7px;
  padding: 9px 14px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
