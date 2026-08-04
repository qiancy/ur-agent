<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  sellerWorkbench,
  type SellerSummary,
  type SellerStockRow,
  type SellerMovement,
} from '../api/seller'
import MetricsRow from '../components/MetricsRow.vue'
import StockTable from '../components/StockTable.vue'
import LowStockPanel from '../components/LowStockPanel.vue'
import ChatPanel from '../components/ChatPanel.vue'
import EntryFormModal from '../components/EntryFormModal.vue'

const summary = ref<SellerSummary | null>(null)
const stock = ref<SellerStockRow[]>([])
const movements = ref<SellerMovement[]>([])
const entryMode = ref<'purchase_in' | 'sales_out' | null>(null)

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
        <div class="status">
          库存估值采用采购均价 · {{ stock.length }} 个库存条目
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

    <MetricsRow :summary="summary" />

    <div class="work">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">库存明细</div>
          <div class="filters">
            <span class="chip">{{ stock.length }} 项</span>
          </div>
        </div>
        <StockTable :rows="stock" :low-stock-threshold="5" />
      </div>

      <aside class="right">
        <LowStockPanel
          :items="summary?.low_stock_items ?? []"
          :stock="stock"
        />
        <div class="panel chat-panel">
          <div class="panel-head">
            <div class="panel-title">Seller AI</div>
            <span class="chip">只读查询</span>
          </div>
          <ChatPanel />
        </div>
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
}
.status {
  color: var(--muted, #637083);
  font-size: 13px;
  margin-top: 5px;
}
.actions {
  display: flex;
  gap: 10px;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 10px 13px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.work {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
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
.right {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
  min-height: 0;
}
.chat-panel {
  min-height: 360px;
}
@media (max-width: 980px) {
  .work {
    grid-template-columns: 1fr;
  }
  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
