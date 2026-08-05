<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ApiError } from '../api/client'
import { sellerSummary, type SellerSummary } from '../api/seller'

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
</script>

<template>
  <section class="summary" data-test="summary">
    <h1 class="summary-title">经营摘要</h1>

    <p v-if="loading" class="summary-hint">加载中…</p>
    <p v-else-if="error" class="form-error" data-test="summary-error">
      {{ error }}
    </p>

    <template v-else-if="summary">
      <div class="metrics">
        <div class="metric">
          <span class="metric-label">销售收入</span>
          <span class="metric-value" data-test="metric-sales">
            {{ summary.sales_amount }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">采购支出</span>
          <span class="metric-value" data-test="metric-purchase">
            {{ summary.purchase_amount }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">净现金流</span>
          <span class="metric-value" data-test="metric-cashflow">
            {{ summary.net_cash_flow }}
          </span>
        </div>
        <div class="metric">
          <span class="metric-label">库存估值</span>
          <span class="metric-value">
            {{ summary.estimated_inventory_value }}
          </span>
        </div>
      </div>

      <div class="panels">
        <div class="panel" data-test="low-stock">
          <h2>低库存商品</h2>
          <ul v-if="summary.low_stock_items.length" class="item-list">
            <li v-for="item in summary.low_stock_items" :key="item.product_uid">
              {{ item.product_uid }} · 余 {{ item.quantity }}{{ item.unit ?? '件' }}
            </li>
          </ul>
          <p v-else class="summary-hint">无低库存商品</p>
        </div>

        <div class="panel" data-test="top-products">
          <h2>热销商品</h2>
          <ul v-if="summary.top_products_by_sales.length" class="item-list">
            <li v-for="p in summary.top_products_by_sales" :key="p.product_uid">
              {{ p.product_uid }} · 销售
              {{ p.sales_amount }}（{{ p.sales_quantity }} 件）
            </li>
          </ul>
          <p v-else class="summary-hint">暂无销售记录</p>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.summary {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px;
}
.summary-title {
  margin: 0 0 18px;
  font-size: 22px;
  color: var(--ink, #17202a);
}
.summary-hint {
  color: var(--muted, #637083);
}
.form-error {
  color: var(--red, #b42318);
}
.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}
.metric {
  padding: 16px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric-label {
  font-size: 12px;
  color: var(--muted, #637083);
}
.metric-value {
  font-size: 22px;
  font-weight: 600;
  color: var(--ink, #17202a);
}
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}
.panel {
  padding: 16px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
}
.panel h2 {
  margin: 0 0 10px;
  font-size: 15px;
  color: var(--ink, #17202a);
}
.item-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  color: var(--ink, #17202a);
}
</style>
