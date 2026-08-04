<script setup lang="ts">
import type { SpaceMember } from '../api/spaceGovernance'

const props = defineProps<{
  members: SpaceMember[]
  currentPuid: string
  role: string
}>()

const emit = defineEmits<{
  (e: 'kick', member: SpaceMember): void
  (e: 'transfer', member: SpaceMember): void
}>()

function isOwner(member: SpaceMember) {
  return member.role === 'owner'
}

function isSelf(member: SpaceMember) {
  return member.puid === props.currentPuid
}

function canKick(member: SpaceMember) {
  if (props.role !== 'owner' && props.role !== 'admin') return false
  if (isSelf(member)) return false
  if (isOwner(member)) return false
  return true
}

function canTransfer(member: SpaceMember) {
  if (props.role !== 'owner') return false
  if (isSelf(member)) return false
  return true
}
</script>

<template>
  <div class="members-table" data-test="members-table">
    <div class="table-head">
      <span class="col name">姓名</span>
      <span class="col puid">PUID</span>
      <span class="col role">角色</span>
      <span class="col joined">加入时间</span>
      <span class="col ops">操作</span>
    </div>
    <div v-for="member in members" :key="member.puid" class="row" data-test="member-row">
      <span class="col name">
        {{ member.name }}
        <span v-if="isSelf(member)" class="self-tag">我</span>
      </span>
      <span class="col puid">{{ member.puid }}</span>
      <span class="col role">
        <span class="role-chip" :class="member.role">{{ member.role }}</span>
      </span>
      <span class="col joined">{{ member.joined_at }}</span>
      <span class="col ops">
        <button
          v-if="canTransfer(member)"
          type="button"
          class="op-btn"
          :data-test="`transfer-${member.puid}`"
          @click="emit('transfer', member)"
        >
          转让
        </button>
        <button
          v-if="canKick(member)"
          type="button"
          class="op-btn danger"
          :data-test="`kick-${member.puid}`"
          @click="emit('kick', member)"
        >
          移除
        </button>
      </span>
    </div>
    <div v-if="members.length === 0" class="empty" data-test="members-empty">
      暂无其他成员
    </div>
  </div>
</template>

<style scoped>
.members-table {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 9px;
  overflow: hidden;
  background: var(--panel, #ffffff);
}
.table-head,
.row {
  display: grid;
  grid-template-columns: 1.4fr 1.2fr 0.8fr 1fr 1fr;
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
.self-tag {
  margin-left: 6px;
  font-size: 11px;
  color: var(--teal, #0f766e);
  border: 1px solid currentColor;
  border-radius: 999px;
  padding: 1px 7px;
}
.role-chip {
  display: inline-block;
  font-size: 12px;
  border-radius: 999px;
  padding: 2px 9px;
  background: #eef2f6;
  color: #40566c;
}
.role-chip.owner {
  background: #fdf0e6;
  color: #b45309;
}
.role-chip.admin {
  background: #e6f1fd;
  color: #1d4f91;
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
