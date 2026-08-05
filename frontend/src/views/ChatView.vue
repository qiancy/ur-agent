<script setup lang="ts">
import ChatPanel from '../components/ChatPanel.vue'
import PageHeader from '../components/PageHeader.vue'
import SectionCard from '../components/SectionCard.vue'
import StatusChip from '../components/StatusChip.vue'

interface Exchange {
  question: string
  answer: string
}

withDefaults(defineProps<{
  headerExchange?: Exchange | null
}>(), {
  headerExchange: null,
})

const QUICK_QUESTIONS = [
  '库存最低的商品是什么？',
  '这个月卖了多少钱？',
  '采购支出是多少？',
  '低库存有哪些？',
]

function onQuickQuestion(question: string) {
  // ChatPanel exposes no programmatic API, so quick questions
  // are informational only. Users must type in ChatPanel's input.
  // The chips serve as suggestion hints.
  console.log('[ChatView] quick question:', question)
}
</script>

<template>
  <section class="chat-view" data-test="chat-view">
    <PageHeader title="Seller AI" status="只读查询" />

    <div v-if="headerExchange" class="panel exchange" data-test="header-exchange">
      <div class="exchange-q">{{ headerExchange.question }}</div>
      <div class="exchange-a">{{ headerExchange.answer }}</div>
    </div>

    <div class="quick-bar">
      <span class="quick-label">快捷提问：</span>
      <button
        v-for="q in QUICK_QUESTIONS"
        :key="q"
        type="button"
        class="quick-chip"
        @click="onQuickQuestion(q)"
      >
        {{ q }}
      </button>
    </div>

    <SectionCard test-id="chat-panel">
      <div class="panel-head">
        <div class="panel-title">Seller AI</div>
        <StatusChip label="只读查询" variant="default" />
      </div>
      <ChatPanel />
    </SectionCard>
  </section>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.quick-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.quick-label {
  font-size: 12px;
  color: var(--muted, #637083);
  font-weight: 600;
  flex-shrink: 0;
}
.quick-chip {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 120ms;
}
.quick-chip:hover {
  background: #f4f6f8;
}
.exchange {
  padding: 14px 16px;
  display: grid;
  gap: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}
.exchange-q {
  font-size: 13px;
  font-weight: 700;
  color: #92400e;
}
.exchange-a {
  font-size: 13px;
  line-height: 1.5;
  color: #78350f;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
}
</style>
