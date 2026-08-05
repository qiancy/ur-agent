<script setup lang="ts">
import type { SellerSummary } from '../api/seller'

const props = defineProps<{
  summary: SellerSummary | null
}>()

function fmt(n: number | undefined | null): string {
  return Number.isFinite(n ?? 0) ? String(n ?? 0) : '0'
}
</script>

<template>
  <section class="metrics">
    <div class="metric">
      <div class="label">销售收入</div>
      <div class="value" data-test="metric-sales">{{ fmt(summary?.sales_amount) }}</div>
      <div class="delta">{{ summary?.sales_count ?? 0 }} 笔</div>
    </div>
    <div class="metric">
      <div class="label">采购支出</div>
      <div class="value" data-test="metric-purchase">{{ fmt(summary?.purchase_amount) }}</div>
      <div class="delta">{{ summary?.purchase_count ?? 0 }} 笔</div>
    </div>
    <div class="metric">
      <div class="label">净现金流</div>
      <div class="value" data-test="metric-cashflow">{{ fmt(summary?.net_cash_flow) }}</div>
      <div class="delta">销售 − 采购</div>
    </div>
    <div class="metric">
      <div class="label">库存估值</div>
      <div class="value" data-test="metric-inventory">{{ fmt(summary?.estimated_inventory_value) }}</div>
      <div class="delta">{{ summary?.stock_location_count ?? 0 }} 个库位</div>
    </div>
    <div class="metric">
      <div class="label">低库存</div>
      <div class="value" data-test="metric-low-stock">{{ summary?.low_stock_items?.length ?? 0 }}</div>
      <div class="delta">阈值 5 件</div>
    </div>
  </section>
</template>

<style scoped>
.metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(140px, 1fr));
  gap: 12px;
}
.metric {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 14px;
}
.metric .label {
  color: var(--muted, #637083);
  font-size: 12px;
}
.metric .value {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 780;
  white-space: nowrap;
}
.metric .delta {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted, #637083);
}
@media (max-width: 980px) {
  .metrics {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
