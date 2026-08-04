<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  getSpaceMembers,
  kickMember,
  transferOwner,
  type SpaceMember,
} from '../api/spaceGovernance'
import MembersTable from '../components/MembersTable.vue'
import InviteMemberModal from '../components/InviteMemberModal.vue'
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
  (e: 'navigate-space', action: string): void
}>()

const members = ref<SpaceMember[]>([])
const loading = ref(true)
const error = ref('')
const showInvite = ref(false)

const pendingKick = ref<SpaceMember | null>(null)
const pendingTransfer = ref<SpaceMember | null>(null)

const isPersonal = computed(() => props.orgType === 'personal')
const canManage = computed(
  () => !isPersonal.value && (props.role === 'owner' || props.role === 'admin'),
)

async function loadMembers() {
  loading.value = true
  error.value = ''
  try {
    const data = await getSpaceMembers()
    members.value = data.members
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载成员失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadMembers)

async function onKickConfirm() {
  const member = pendingKick.value
  if (!member) return
  pendingKick.value = null
  try {
    await kickMember(props.ouid, member.puid)
    await loadMembers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '移除失败'
  }
}

async function onTransferConfirm() {
  const member = pendingTransfer.value
  if (!member) return
  pendingTransfer.value = null
  try {
    await transferOwner(props.ouid, member.puid)
    await loadMembers()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '转让失败'
  }
}

function onInvited() {
  loadMembers()
}

const copied = ref(false)

async function copyOuid() {
  copied.value = false
  try {
    await navigator.clipboard.writeText(props.ouid)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 1500)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <section class="space-manage-view" data-test="space-manage-view">
    <div class="head">
      <div>
        <h2 class="title">管理空间</h2>
        <p class="sub">{{ organizationName }} · {{ ouid }}</p>
      </div>
      <button
        type="button"
        class="btn"
        data-test="create-space"
        @click="emit('navigate-space', 'create')"
      >
        创建空间
      </button>
    </div>

    <div class="card info-card" data-test="space-info">
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">空间名称</span>
          <span class="info-value">{{ organizationName }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">OUID</span>
          <span class="info-value ouid-cell">
            {{ ouid }}
            <button
              type="button"
              class="copy-btn"
              data-test="copy-ouid"
              @click="copyOuid"
            >
              {{ copied ? '已复制' : '复制' }}
            </button>
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">类型</span>
          <span class="info-value">{{ orgType }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">我的角色</span>
          <span class="info-value">{{ role }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">成员数</span>
          <span class="info-value">{{ members.length }}</span>
        </div>
      </div>
      <p v-if="isPersonal" class="hint" data-test="personal-hint">
        个人空间由注册时自动创建，仅本人可见，不可邀请或退出。
      </p>
    </div>

    <div class="card">
      <div class="card-head">
        <h3 class="card-title">成员列表</h3>
        <button
          v-if="canManage"
          type="button"
          class="btn primary"
          data-test="invite-member"
          @click="showInvite = true"
        >
          邀请成员
        </button>
      </div>
      <p v-if="error" class="error" data-test="manage-error">{{ error }}</p>
      <MembersTable
        :members="members"
        :current-puid="puid"
        :role="role"
        @kick="pendingKick = $event"
        @transfer="pendingTransfer = $event"
      />
    </div>

    <InviteMemberModal
      :open="showInvite"
      :ouid="ouid"
      @invited="onInvited"
      @close="showInvite = false"
    />

    <ConfirmDialog
      :open="pendingKick !== null"
      title="移除成员"
      :message="`确定将 ${pendingKick?.name ?? ''}（${pendingKick?.puid ?? ''}）移出该空间？`"
      confirm-label="移除"
      danger
      @confirm="onKickConfirm"
      @cancel="pendingKick = null"
    />

    <ConfirmDialog
      :open="pendingTransfer !== null"
      title="转让所有权"
      :message="`确定将空间所有权转让给 ${pendingTransfer?.name ?? ''}（${pendingTransfer?.puid ?? ''}）？转让后您将成为 admin。`"
      confirm-label="转让"
      @confirm="onTransferConfirm"
      @cancel="pendingTransfer = null"
    />
  </section>
</template>

<style scoped>
.space-manage-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}
.sub {
  margin: 2px 0 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  padding: 18px;
}
.info-card {
  padding: 18px;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-label {
  font-size: 12px;
  color: var(--muted, #637083);
}
.info-value {
  font-size: 14px;
  font-weight: 650;
  word-break: break-all;
}
.ouid-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.copy-btn {
  flex: none;
  font-size: 12px;
  padding: 2px 8px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 6px;
  background: var(--surface, #fff);
  color: var(--accent, #2563eb);
  cursor: pointer;
}
.copy-btn:hover {
  background: var(--bg-soft, #f5f7fa);
}
.hint {
  margin: 14px 0 0;
  font-size: 12px;
  color: var(--muted, #637083);
  border-top: 1px solid var(--line, #d8dee8);
  padding-top: 12px;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 750;
}
.error {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--red, #b42318);
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
</style>
