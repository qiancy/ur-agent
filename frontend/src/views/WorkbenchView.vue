<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  sellerWorkbench,
  type SellerSummary,
  type SellerStockRow,
  type SellerMovement,
} from '../api/seller'
import MetricTile from '../components/MetricTile.vue'
import SnapshotLine from '../components/SnapshotLine.vue'
import AiInsightCard from '../components/AiInsightCard.vue'
import StockTable from '../components/StockTable.vue'
import LowStockPanel from '../components/LowStockPanel.vue'
import EntryFormModal from '../components/EntryFormModal.vue'

const summary = ref<SellerSummary | null>(null)
const stock = ref<SellerStockRow[]>([])
const movements = ref<SellerMovement[]>([])
const entryMode = ref<'purchase_in' | 'sales_out' | null>(null)

const snapshotTime = computed(() => {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`
})

const insights = computed(() => {
  const items: string[] = []
  if (summary.value) {
    const lowCount = summary.value.low_stock_items?.length ?? 0
    if (lowCount > 0) {
      items.push(`当前有 ${lowCount} 个商品处于低库存状态，建议尽快补货。`)
    }
    if ((summary.value.net_cash_flow ?? 0) < 0) {
      items.push('净现金流为负，请注意控制采购支出。')
    }
    if ((summary.value.movement_count ?? 0) === 0) {
      items.push('暂无流水记录，请先进行入库或出库操作。')
    }
  }
  return items
})

function fmt(n: number | undefined | null): string {
  return Number.isFinite(n ?? 0) ? String(n ?? 0) : '0'
}

async function loadAll() {
  const data = await sellerWorkbench({ movementsLimit: 10 })
  summary.value = data.summary
  stock.value = data.stock
  movements.value = data.movements
}

onMounted(loadAll)

function openEntry(mode: 'purchase_in' | 'sales_out') {
  entryMode.value = mode
}

async function onSubmitted() {
  entryMode.value = null
  await loadAll()
}
</script>

<template>
  <section class="workbench" data-test="workbench">
    <div class="topbar">
      <div>
        <h1>经营工作台</h1>
        <div class="sub">
          <SnapshotLine :time="snapshotTime" label="快照" />
          <span class="sep">·</span>
          <span class="hint">库存估值采用采购均价 · {{ stock.length }} 个库存条目</span>
        </div>
      </div>
      <div class="actions">
        <button class="btn" type="button" data-test="btn-sales" @click="openEntry('sales_out')">
          出库
        </button>
        <button class="btn primary" type="button" data-test="btn-purchase" @click="openEntry('purchase_in')">
          入库
        </button>
      </div>
    </div>

    <div class="kpi-row">
      <MetricTile
        label="销售收入"
        :value="fmt(summary?.sales_amount)"
        trend="↑12%"
        accent="success"
        data-test="metric-sales"
      />
      <MetricTile
        label="采购支出"
        :value="fmt(summary?.purchase_amount)"
        :trend="`${summary?.purchase_count ?? 0} 笔`"
        data-test="metric-purchase"
      />
      <MetricTile
        label="净现金流"
        :value="fmt(summary?.net_cash_flow)"
        accent="danger"
        data-test="metric-cashflow"
      />
      <MetricTile
        label="库存估值"
        :value="fmt(summary?.estimated_inventory_value)"
        :trend="`${summary?.stock_location_count ?? 0} 个库位`"
        data-test="metric-inventory"
      />
      <MetricTile
        label="低库存数量"
        :value="summary?.low_stock_items?.length ?? 0"
        accent="warning"
        data-test="metric-low-stock"
      />
    </div>

    <div class="work">
      <div class="main-col">
        <section class="panel" data-test="stock-panel">
          <div class="panel-head">
            <div class="panel-title">库存明细</div>
            <div class="filters">
              <span class="chip">{{ stock.length }} 项</span>
            </div>
          </div>
          <StockTable :rows="stock" :low-stock-threshold="5" />
        </section>

        <section class="panel" data-test="movements-panel">
          <div class="panel-head">
            <div class="panel-title">最近流水</div>
            <span class="chip">{{ movements.length }} 条</span>
          </div>
          <div v-if="movements.length" class="movement-list">
            <div v-for="m in movements" :key="m.movement_uid" class="movement" :data-test="`movement-${m.movement_uid}`">
              <span class="movement-type" :class="m.operation_type">{{ m.operation_type === 'purchase_in' ? '入库' : '出库' }}</span>
              <span class="movement-product">{{ m.product_uid }}</span>
              <span class="movement-delta" :class="{ positive: m.quantity_delta > 0, negative: m.quantity_delta < 0 }">
                {{ m.quantity_delta > 0 ? '+' : '' }}{{ m.quantity_delta }}{{ m.unit }}
              </span>
              <span class="movement-amount">{{ m.total_amount }}</span>
              <span class="movement-where">{{ m.warehouse_code }} / {{ m.location_path }}</span>
            </div>
          </div>
          <p v-else class="hint">暂无流水</p>
        </section>
      </div>

      <aside class="right">
        <LowStockPanel
          :items="summary?.low_stock_items ?? []"
          :stock="stock"
        />
        <AiInsightCard
          title="AI 经营摘要"
          :items="insights"
          variant="warning"
        />
      </aside>
    </div>

    <EntryFormModal
      v-if="entryMode"
      :mode="entryMode"
      @submitted="onSubmitted"
      @close="entryMode = null"
    />
  </section>
</template>

<style scoped>
.workbench {
  display: grid;
  gap: 16px;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 750;
  line-height: 1.3;
}
.sub {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 13px;
  color: var(--muted, #637083);
}
.sep {
  color: var(--line, #d8dee8);
}
.actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 10px 18px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn.primary:hover {
  background: #115e59;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(140px, 1fr));
  gap: 12px;
}
.work {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
  align-items: start;
}
.main-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.right {
  display: grid;
  gap: 16px;
  min-width: 0;
  position: sticky;
  top: 76px;
}
.panel {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  min-width: 0;
  overflow: hidden;
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
  font-weight: 700;
  color: var(--ink, #17202a);
}
.filters {
  display: flex;
  gap: 8px;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
}
.movement-list {
  display: flex;
  flex-direction: column;
}
.movement {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  flex-wrap: wrap;
}
.movement:last-child {
  border-bottom: 0;
}
.movement-type {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.movement-type:deep(.purchase_in) {
  background: #ecfdf5;
  color: #047857;
}
.movement-type:deep(.sales_out) {
  background: #fef2f2;
  color: #b42318;
}
.movement-product {
  font-weight: 650;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.movement-delta {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  min-width: 60px;
  text-align: right;
}
.movement-delta.positive {
  color: #047857;
}
.movement-delta.negative {
  color: #b42318;
}
.movement-amount {
  color: var(--muted, #637083);
  font-variant-numeric: tabular-nums;
  min-width: 70px;
  text-align: right;
}
.movement-where {
  color: var(--muted, #637083);
  font-size: 12px;
  margin-left: auto;
}
.hint {
  margin: 0;
  padding: 16px;
  color: var(--muted, #637083);
  font-size: 13px;
}
@media (max-width: 1280px) {
  .kpi-row {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 980px) {
  .work {
    grid-template-columns: 1fr;
  }
  .right {
    position: static;
  }
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
