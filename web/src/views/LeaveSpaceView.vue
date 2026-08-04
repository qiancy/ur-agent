<script setup lang="ts">
import { ref } from 'vue'
import { leaveSpace } from '../api/spaceGovernance'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const props = defineProps<{
  ouid: string
  orgType: string
  role: string
  puid: string
  personName: string
  organizationName: string
}>()

const emit = defineEmits<{
  (e: 'leave-confirmed'): void
  (e: 'navigate-space', action: string): void
}>()

const showConfirm = ref(false)
const loading = ref(false)
const error = ref('')

async function onConfirm() {
  error.value = ''
  loading.value = true
  try {
    await leaveSpace(props.ouid)
    emit('leave-confirmed')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '退出失败'
  } finally {
    loading.value = false
    showConfirm.value = false
  }
}
</script>

<template>
  <section class="leave-space-view" data-test="leave-space-view">
    <div class="card">
      <h2 class="title">退出空间</h2>
      <p class="text">
        即将退出空间 <strong>{{ organizationName }}</strong>（{{ ouid }}）。
        退出后你将无法查看该空间的数据；如需重新加入，需要再次被邀请或重新申请。
      </p>
      <p v-if="role === 'owner'" class="warn" data-test="owner-warn">
        你是该空间的 owner。若你是唯一 owner，请先在「管理空间」中将所有权转让给其他成员。
      </p>
      <p v-if="error" class="error" data-test="leave-error">{{ error }}</p>
      <div class="actions">
        <button
          type="button"
          class="btn"
          data-test="leave-back"
          @click="emit('navigate-space', 'manage')"
        >
          返回管理
        </button>
        <button
          type="button"
          class="btn danger"
          :disabled="loading"
          data-test="leave-confirm-open"
          @click="showConfirm = true"
        >
          {{ loading ? '退出中…' : '确认退出' }}
        </button>
      </div>
    </div>

    <ConfirmDialog
      :open="showConfirm"
      title="退出空间"
      :message="`确定退出「${organizationName}」？`"
      confirm-label="退出"
      danger
      @confirm="onConfirm"
      @cancel="showConfirm = false"
    />
  </section>
</template>

<style scoped>
.leave-space-view {
  max-width: 560px;
}
.card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}
.text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink, #17202a);
}
.warn {
  margin: 0;
  font-size: 13px;
  color: #946800;
  background: #fdf3d7;
  border-radius: 8px;
  padding: 10px 12px;
}
.error {
  margin: 0;
  font-size: 13px;
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
.btn.danger {
  background: var(--red, #b42318);
  color: #ffffff;
  border-color: var(--red, #b42318);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
