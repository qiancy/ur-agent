<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { sellerStock, type SellerStockRow } from '../api/seller'
import PageHeader from '../components/PageHeader.vue'
import SectionCard from '../components/SectionCard.vue'
import EmptyState from '../components/EmptyState.vue'
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
    <PageHeader
      title="库存"
      :status="`${rows.length} 个库存条目`"
    >
      <button class="btn" type="button" data-test="btn-refresh" @click="load">
        刷新
      </button>
    </PageHeader>

    <SectionCard test-id="stock-panel">
      <template #filters>
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
      </template>

      <p v-if="loading" class="hint">加载中…</p>
      <StockTable v-else-if="rows.length" :rows="rows" :low-stock-threshold="5" />
      <EmptyState
        v-else
        type="filtered"
        title="暂无库存数据"
        description="当前筛选条件下没有库存记录，请尝试其他筛选条件。"
      />
    </SectionCard>
  </section>
</template>

<style scoped>
.stock-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
.btn:hover {
  background: #f4f6f8;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
}
.hint {
  padding: 16px;
  color: var(--muted, #637083);
  font-size: 13px;
  margin: 0;
}
</style>
