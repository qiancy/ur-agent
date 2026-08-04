<script setup lang="ts">
import { reactive, ref } from 'vue'
import { createInvite, type SpaceInvite } from '../api/spaceGovernance'

const props = defineProps<{
  open: boolean
  ouid: string
}>()

const emit = defineEmits<{
  (e: 'invited', invite: SpaceInvite): void
  (e: 'close'): void
}>()

const loading = ref(false)
const error = ref('')
const form = reactive({
  invitee_puid: '',
  role: 'member',
})

function onClose() {
  error.value = ''
  form.invitee_puid = ''
  form.role = 'member'
  emit('close')
}

async function onSubmit() {
  error.value = ''
  const puid = form.invitee_puid.trim()
  if (!puid) {
    error.value = '请填写受邀人的 PUID'
    return
  }
  loading.value = true
  try {
    const invite = await createInvite(props.ouid, puid, form.role)
    emit('invited', invite as unknown as SpaceInvite)
    onClose()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '邀请失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="open" class="mask" data-test="invite-modal" @click.self="onClose">
    <div class="modal" role="dialog" aria-label="邀请成员">
      <div class="head">
        <div class="title">邀请成员</div>
        <button class="close" type="button" data-test="invite-close" @click="onClose">×</button>
      </div>
      <form class="body" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field-label">受邀人 PUID</span>
          <input
            v-model="form.invitee_puid"
            data-test="invitee-puid"
            type="text"
            placeholder="例如 zhangsan"
            autocomplete="off"
          />
        </label>
        <label class="field">
          <span class="field-label">角色</span>
          <select v-model="form.role" class="select" data-test="invite-role">
            <option value="member">member</option>
            <option value="viewer">viewer</option>
          </select>
        </label>
        <p v-if="error" class="form-error" data-test="invite-error">{{ error }}</p>
        <div class="actions">
          <button type="button" class="btn" data-test="invite-cancel" @click="onClose">取消</button>
          <button type="submit" class="btn primary" :disabled="loading" data-test="invite-submit">
            {{ loading ? '发送中…' : '发送邀请' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(22, 32, 46, 0.45);
  display: grid;
  place-items: center;
  z-index: 110;
}
.modal {
  width: 380px;
  max-width: 92vw;
  background: var(--panel, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--line, #d8dee8);
  box-shadow: 0 12px 40px rgba(22, 32, 46, 0.2);
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 18px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.title {
  font-size: 16px;
  font-weight: 750;
}
.close {
  border: 0;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--muted, #637083);
  cursor: pointer;
}
.body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 13px;
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
  padding: 9px 11px;
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
.form-error {
  margin: 0;
  font-size: 12px;
  color: var(--red, #b42318);
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
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
