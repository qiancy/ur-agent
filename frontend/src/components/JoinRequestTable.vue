<script setup lang="ts">
import type { SpaceJoinRequest } from '../api/spaceGovernance'

const props = defineProps<{
  requests: SpaceJoinRequest[]
  canApprove: boolean
}>()

const emit = defineEmits<{
  (e: 'approve', request: SpaceJoinRequest): void
  (e: 'reject', request: SpaceJoinRequest): void
}>()
</script>

<template>
  <div class="req-table" data-test="join-request-table">
    <div class="table-head">
      <span class="col who">申请人</span>
      <span class="col msg">留言</span>
      <span class="col time">申请时间</span>
      <span v-if="canApprove" class="col ops">操作</span>
    </div>
    <div v-for="req in requests" :key="req.request_uid" class="row" data-test="join-request-row">
      <span class="col who">
        <span class="name">{{ req.requester_name || '未知用户' }}</span>
        <span class="puid">{{ req.requester_puid }}</span>
      </span>
      <span class="col msg">{{ req.message || '—' }}</span>
      <span class="col time">{{ req.created_at }}</span>
      <span v-if="canApprove" class="col ops">
        <button
          type="button"
          class="op-btn"
          :data-test="`approve-${req.request_uid}`"
          @click="emit('approve', req)"
        >
          通过
        </button>
        <button
          type="button"
          class="op-btn danger"
          :data-test="`reject-${req.request_uid}`"
          @click="emit('reject', req)"
        >
          拒绝
        </button>
      </span>
    </div>
    <div v-if="requests.length === 0" class="empty" data-test="join-requests-empty">
      暂无待处理的申请
    </div>
  </div>
</template>

<style scoped>
.req-table {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 9px;
  overflow: hidden;
  background: var(--panel, #ffffff);
}
.table-head,
.row {
  display: grid;
  grid-template-columns: 1.2fr 1.6fr 1fr 1fr;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
}
.table-head {
  background: #f7f9fb;
  font-size: 12px;
  color: var(--muted, #637083);
  font-weight: 650;
}
.row {
  border-top: 1px solid var(--line, #d8dee8);
  font-size: 13px;
}
.col {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.who {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.name {
  font-weight: 650;
}
.puid {
  color: var(--muted, #637083);
  font-size: 12px;
}
.msg {
  color: var(--ink, #17202a);
  white-space: normal;
}
.op-btn {
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  margin-right: 6px;
}
.op-btn:hover {
  background: #f4f6f8;
}
.op-btn.danger {
  color: var(--red, #b42318);
  border-color: #f2b8b5;
}
.empty {
  padding: 22px;
  text-align: center;
  color: var(--muted, #637083);
  font-size: 13px;
}
</style>
