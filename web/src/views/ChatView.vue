<script setup lang="ts">
import ChatPanel from '../components/ChatPanel.vue'
</script>

<template>
  <section class="chat-view" data-test="chat-view">
    <h1 class="page-title">Seller AI</h1>
    <p class="status">只读经营查询 · 写入操作请使用入库/出库表单</p>
    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">Seller AI</div>
        <span class="chip">只读查询</span>
      </div>
      <ChatPanel />
    </div>
  </section>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 750;
}
.status {
  color: var(--muted, #637083);
  font-size: 13px;
  margin: 0;
}
.panel {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  min-width: 0;
}
.panel-head {
  min-height: 54px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.panel-title {
  font-size: 15px;
  font-weight: 760;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
}
</style>
