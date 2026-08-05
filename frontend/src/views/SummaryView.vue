<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError } from '../api/client'
import { sellerSummary, type SellerSummary } from '../api/seller'
import PageHeader from '../components/PageHeader.vue'
import MetricTile from '../components/MetricTile.vue'
import SectionCard from '../components/SectionCard.vue'
import StatusChip from '../components/StatusChip.vue'
import EmptyState from '../components/EmptyState.vue'

const emit = defineEmits<{
  (e: 'logged-out'): void
}>()

const summary = ref<SellerSummary | null>(null)
const error = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    summary.value = await sellerSummary()
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      emit('logged-out')
    } else {
      error.value = e instanceof Error ? e.message : '摘要加载失败'
    }
  } finally {
    loading.value = false
  }
})

function fmt(n: number | undefined | null): string {
  return Number.isFinite(n ?? 0) ? String(n ?? 0) : '0'
}
</script>

<template>
  <section class="summary" data-test="summary">
    <PageHeader title="经营摘要" />

    <p v-if="loading" class="summary-hint">加载中…</p>
    <p v-else-if="error" class="form-error" data-test="summary-error">
      {{ error }}
    </p>

    <template v-else-if="summary">
      <div class="kpi-row">
        <MetricTile
          label="销售收入"
          :value="fmt(summary.sales_amount)"
          trend="↑12%"
          accent="success"
          data-test="metric-sales"
        />
        <MetricTile
          label="采购支出"
          :value="fmt(summary.purchase_amount)"
          data-test="metric-purchase"
        />
        <MetricTile
          label="净现金流"
          :value="fmt(summary.net_cash_flow)"
          :accent="summary.net_cash_flow < 0 ? 'danger' : 'default'"
          data-test="metric-cashflow"
        />
        <MetricTile
          label="库存估值"
          :value="fmt(summary.estimated_inventory_value)"
          data-test="metric-inventory"
        />
      </div>

      <div class="panels">
        <SectionCard title="低库存商品" data-test="low-stock">
          <ul v-if="summary.low_stock_items.length" class="item-list">
            <li v-for="item in summary.low_stock_items" :key="item.product_uid" class="item" data-test="low-stock-item">
              <div class="item-head">
                <span class="item-name">{{ item.product_uid }}</span>
                <StatusChip :label="`余 ${item.quantity}${item.unit ?? '件'}`" variant="warning" />
              </div>
              <div class="item-bar">
                <div class="bar" :style="{ width: `${Math.min(100, (item.quantity / 10) * 100)}%` }" />
              </div>
            </li>
          </ul>
          <EmptyState
            v-else
            type="readonly"
            title="无低库存商品"
            description="当前所有商品库存充足。"
          />
        </SectionCard>

        <SectionCard title="热销商品" data-test="top-products">
          <ul v-if="summary.top_products_by_sales.length" class="item-list">
            <li v-for="p in summary.top_products_by_sales" :key="p.product_uid" class="item" data-test="top-product-item">
              <div class="item-head">
                <span class="item-name">{{ p.product_uid }}</span>
                <StatusChip label="热销" variant="ok" />
              </div>
              <div class="item-meta">
                销售 {{ p.sales_amount }}（{{ p.sales_quantity }} 件）
              </div>
              <div class="item-bar">
                <div class="bar is-teal" :style="{ width: `${Math.min(100, (p.sales_quantity / Math.max(1, summary.top_products_by_sales[0].sales_quantity)) * 100)}%` }" />
              </div>
            </li>
          </ul>
          <EmptyState
            v-else
            type="readonly"
            title="暂无销售记录"
            description="完成出库操作后，销售数据将在此显示。"
          />
        </SectionCard>
      </div>
    </template>
  </section>
</template>

<style scoped>
.summary {
  max-width: 860px;
  margin: 0 auto;
}
.summary-hint {
  color: var(--muted, #637083);
}
.form-error {
  color: var(--red, #b42318);
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}
.item-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.item-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--ink, #17202a);
}
.item-meta {
  font-size: 12px;
  color: var(--muted, #637083);
}
.item-bar {
  height: 4px;
  border-radius: 2px;
  background: #f1f5f9;
  overflow: hidden;
}
.bar {
  height: 100%;
  border-radius: 2px;
  background: var(--amber, #f59e0b);
  transition: width 300ms ease;
}
.bar.is-teal {
  background: var(--teal, #0f766e);
}
@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
