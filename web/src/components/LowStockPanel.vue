<script setup lang="ts">
import { computed } from 'vue'
import type { SellerStockRow } from '../api/seller'

const props = defineProps<{
  items: { product_uid: string; quantity: number; unit: string | null }[]
  stock: SellerStockRow[]
}>()

const sorted = computed(() =>
  [...props.items].sort((a, b) => Number(a.quantity) - Number(b.quantity)),
)

function locationOf(productUid: string): string {
  const row = props.stock.find((r) => r.product_uid === productUid)
  return row ? `${row.warehouse_code} · ${row.location_path}` : ''
}
</script>

<template>
  <div class="panel low-panel">
    <div class="panel-head">
      <div class="panel-title">低库存处理</div>
      <span class="chip">{{ sorted.length }} 项</span>
    </div>
    <div class="low-list">
      <div v-for="item in sorted" :key="item.product_uid" class="low-item">
        <div>
          {{ item.product_uid }}<br />
          <span class="loc">{{ locationOf(item.product_uid) }}</span>
        </div>
        <strong>{{ item.quantity }} {{ item.unit ?? '件' }}</strong>
      </div>
      <p v-if="sorted.length === 0" class="empty-hint">暂无低库存</p>
    </div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
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
.low-list {
  display: grid;
  gap: 10px;
  padding: 14px;
}
.low-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #edf0f4;
  font-size: 13px;
  align-items: center;
}
.low-item:last-child {
  border-bottom: 0;
}
.loc {
  color: var(--muted, #637083);
  font-size: 12px;
}
.empty-hint {
  margin: 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
</style>
