<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { sellerStock, type SellerStockRow } from '../api/seller'
import StockTable from '../components/StockTable.vue'

const rows = ref<SellerStockRow[]>([])
const loading = ref(true)
const productFilter = ref('')

async function load() {
  loading.value = true
  try {
    const q = productFilter.value.trim()
    rows.value = q ? await sellerStock(q) : await sellerStock()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="stock-view" data-test="stock-view">
    <div class="topbar">
      <div>
        <h1>库存</h1>
        <div class="status">{{ rows.length }} 个库存条目</div>
      </div>
      <button class="btn" type="button" data-test="btn-refresh" @click="load">
        刷新
      </button>
    </div>
    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">全部库存</div>
        <div class="filters">
          <input
            v-model="productFilter"
            data-test="filter-product"
            type="text"
            placeholder="按商品筛选"
            @keyup.enter="load"
          />
          <button class="btn" type="button" data-test="btn-filter" @click="load">
            筛选
          </button>
          <span class="chip">低库存阈值 5 件</span>
        </div>
      </div>
      <p v-if="loading" class="hint">加载中…</p>
      <StockTable v-else :rows="rows" :low-stock-threshold="5" />
    </div>
  </section>
</template>

<style scoped>
.stock-view {
  display: flex;
  flex-direction: column;
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
.filters {
  display: flex;
  gap: 8px;
  align-items: center;
}
.filters input {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 6px;
  padding: 9px 11px;
  font-size: 13px;
}
.hint {
  padding: 16px;
  color: var(--muted, #637083);
  font-size: 13px;
  margin: 0;
}
</style>
