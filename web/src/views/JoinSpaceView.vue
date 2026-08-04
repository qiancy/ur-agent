<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  acceptInvite,
  createJoinRequest,
  getMyInvites,
  getMyJoinRequests,
  type MyJoinRequest,
  type SpaceInvite,
} from '../api/spaceGovernance'
import { switchOrganization } from '../api/auth'
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
}>()

const tab = ref<'invites' | 'requests'>('invites')
const invites = ref<SpaceInvite[]>([])
const myRequests = ref<MyJoinRequest[]>([])
const loading = ref(true)
const error = ref('')

const inviteForm = ref({ invite_uid: '' })
const form = ref({ ouid: '', message: '' })
const submitting = ref(false)
const accepting = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [invitesData, requestsData] = await Promise.all([
      getMyInvites('pending'),
      getMyJoinRequests('pending'),
    ])
    invites.value = invitesData.invites
    myRequests.value = requestsData.requests
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function onAccept(invite: SpaceInvite) {
  error.value = ''
  accepting.value = true
  try {
    await acceptInvite(invite.invite_uid)
    const result = await switchOrganization(invite.ouid)
    emit('context-updated', result)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '接受邀请失败'
  } finally {
    accepting.value = false
  }
}

async function onAcceptByUid() {
  error.value = ''
  const inviteUid = inviteForm.value.invite_uid.trim()
  if (!inviteUid) {
    error.value = '请填写邀请码 invite_uid'
    return
  }
  accepting.value = true
  try {
    const result = await acceptInvite(inviteUid)
    if (result.ouid) {
      const switched = await switchOrganization(result.ouid)
      emit('context-updated', switched)
    } else {
      await load()
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '接受邀请失败'
  } finally {
    accepting.value = false
  }
}

async function onSubmit() {
  error.value = ''
  const ouid = form.value.ouid.trim()
  if (!ouid) {
    error.value = '请填写要加入的空间 OUID'
    return
  }
  submitting.value = true
  try {
    await createJoinRequest(ouid, form.value.message.trim() || undefined)
    form.value.ouid = ''
    form.value.message = ''
    const requestsData = await getMyJoinRequests('pending')
    myRequests.value = requestsData.requests
  } catch (e) {
    error.value = e instanceof Error ? e.message : '申请失败'
  } finally {
    submitting.value = false
  }
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    accepted: '已接受',
    declined: '已拒绝',
  }
  return map[status] ?? status
}
</script>

<template>
  <section class="join-space-view" data-test="join-space-view">
    <h2 class="title">加入空间</h2>

    <div class="tabs" role="tablist">
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'invites' }"
        role="tab"
        :aria-selected="tab === 'invites'"
        data-test="tab-invites"
        @click="tab = 'invites'"
      >
        收到的邀请
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'requests' }"
        role="tab"
        :aria-selected="tab === 'requests'"
        data-test="tab-requests"
        @click="tab = 'requests'"
      >
        我的申请
      </button>
    </div>

    <p v-if="error" class="error" data-test="join-error">{{ error }}</p>

    <div v-if="tab === 'invites'" class="card" data-test="invites-panel">
      <form class="accept-form" @submit.prevent="onAcceptByUid">
        <label class="field">
          <span class="field-label">邀请码 invite_uid</span>
          <input
            v-model="inviteForm.invite_uid"
            data-test="accept-invite-uid"
            type="text"
            placeholder="例如 inv_a1b2c3d4"
            autocomplete="off"
          />
        </label>
        <button type="submit" class="btn primary" :disabled="accepting" data-test="accept-by-uid">
          {{ accepting ? '处理中…' : '接受邀请' }}
        </button>
      </form>

      <div v-if="invites.length === 0 && !loading" class="empty" data-test="invites-empty">
        暂无待处理的邀请
      </div>
      <div v-for="invite in invites" :key="invite.invite_uid" class="invite-row" data-test="invite-row">
        <div class="invite-info">
          <div class="invite-name">{{ invite.organization_name }}</div>
          <div class="invite-meta">
            {{ invite.ouid }} · {{ invite.organization_type }} · 角色 {{ invite.role }} ·
            {{ invite.created_by_puid }} 邀请
          </div>
        </div>
        <button
          type="button"
          class="btn primary"
          :disabled="accepting"
          :data-test="`accept-${invite.invite_uid}`"
          @click="onAccept(invite)"
        >
          接受
        </button>
      </div>
    </div>

    <div v-else class="card apply-panel" data-test="requests-panel">
      <form class="apply-form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field-label">要加入的空间 OUID *</span>
          <input
            v-model="form.ouid"
            data-test="apply-ouid"
            type="text"
            placeholder="例如 family_learning"
            autocomplete="off"
          />
        </label>
        <label class="field">
          <span class="field-label">申请留言（可选）</span>
          <input
            v-model="form.message"
            data-test="apply-message"
            type="text"
            placeholder="介绍下自己"
            autocomplete="off"
          />
        </label>
        <button type="submit" class="btn primary" :disabled="submitting" data-test="apply-submit">
          {{ submitting ? '提交中…' : '提交申请' }}
        </button>
      </form>

      <div v-if="myRequests.length === 0 && !loading" class="empty" data-test="requests-empty">
        暂无申请记录
      </div>
      <div v-for="req in myRequests" :key="req.request_uid" class="invite-row" data-test="my-request-row">
        <div class="invite-info">
          <div class="invite-name">{{ req.organization_name }}</div>
          <div class="invite-meta">
            {{ req.ouid }} · {{ req.organization_type }} · {{ req.message || '无留言' }}
          </div>
        </div>
        <span class="status-chip" :class="req.status" :data-test="`req-status-${req.request_uid}`">
          {{ statusLabel(req.status) }}
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.join-space-view {
  max-width: 720px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}
.tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.tab {
  border: 0;
  background: transparent;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 650;
  color: var(--muted, #637083);
  cursor: pointer;
  border-bottom: 2px solid transparent;
}
.tab.active {
  color: var(--teal, #0f766e);
  border-bottom-color: var(--teal, #0f766e);
}
.card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  padding: 18px;
}
.invite-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.invite-row:last-child {
  border-bottom: 0;
}
.invite-name {
  font-size: 14px;
  font-weight: 700;
}
.invite-meta {
  margin-top: 2px;
  font-size: 12px;
  color: var(--muted, #637083);
}
.empty {
  padding: 20px;
  text-align: center;
  color: var(--muted, #637083);
  font-size: 13px;
}
.error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
.apply-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line, #d8dee8);
  margin-bottom: 6px;
}
.accept-form {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line, #d8dee8);
  margin-bottom: 6px;
}
.accept-form .field {
  flex: 1;
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
input {
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
.status-chip {
  font-size: 12px;
  border-radius: 999px;
  padding: 3px 10px;
  background: #eef2f6;
  color: #40566c;
}
.status-chip.pending {
  background: #fdf3d7;
  color: #946800;
}
.status-chip.approved,
.status-chip.accepted {
  background: #e7f5ee;
  color: #0f766e;
}
.status-chip.rejected,
.status-chip.declined {
  background: #fdecec;
  color: #b42318;
}
</style>
