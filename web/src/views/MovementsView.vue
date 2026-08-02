<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { sellerInventoryMovements, type SellerMovement } from '../api/seller'
import MovementTable from '../components/MovementTable.vue'

const rows = ref<SellerMovement[]>([])
const loading = ref(true)
const filterOperation = ref('')

async function load() {
  loading.value = true
  try {
    rows.value = await sellerInventoryMovements(
      filterOperation.value ? { operationType: filterOperation.value } : {},
    )
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(filterOperation, load)
</script>

<template>
  <section class="movements-view" data-test="movements-view">
    <div class="topbar">
      <div>
        <h1>库存流水</h1>
        <div class="status">{{ rows.length }} 条记录</div>
      </div>
      <div class="filters">
        <select v-model="filterOperation" data-test="filter-operation">
          <option value="">全部类型</option>
          <option value="purchase_in">入库</option>
          <option value="sales_out">出库</option>
        </select>
        <button class="btn" type="button" data-test="btn-refresh" @click="load">
          刷新
        </button>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">最近流水</div>
        <div class="filters">
          <span class="chip">{{ rows.length }} 条</span>
        </div>
      </div>
      <p v-if="loading" class="hint">加载中…</p>
      <MovementTable v-else :rows="rows" />
    </div>
  </section>
</template>

<style scoped>
.movements-view {
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
.filters {
  display: flex;
  gap: 8px;
  align-items: center;
}
select {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 6px;
  padding: 9px 11px;
  font-size: 13px;
  background: var(--panel, #ffffff);
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
.hint {
  padding: 16px;
  color: var(--muted, #637083);
  font-size: 13px;
  margin: 0;
}
</style>
