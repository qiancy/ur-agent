<script setup lang="ts">
import type { SellerStockRow } from '../api/seller'

const props = defineProps<{
  rows: SellerStockRow[]
  lowStockThreshold?: number
}>()

function status(row: SellerStockRow): { tag: string; label: string } {
  const threshold = props.lowStockThreshold ?? 5
  const qty = Number(row.quantity)
  if (qty < threshold) {
    return { tag: 'danger', label: '低库存' }
  }
  if (qty === threshold) {
    return { tag: 'warn', label: '临界' }
  }
  return { tag: 'ok', label: '充足' }
}
</script>

<template>
  <table class="stock-table">
    <thead>
      <tr>
        <th>商品</th>
        <th>仓库</th>
        <th>库位</th>
        <th class="num">数量</th>
        <th>单位</th>
        <th>状态</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.product_uid + row.warehouse_code + row.location_path">
        <td>{{ row.product_uid }}</td>
        <td>{{ row.warehouse_code }}</td>
        <td>{{ row.location_path }}</td>
        <td class="num">{{ row.quantity }}</td>
        <td>{{ row.unit }}</td>
        <td><span class="tag" :class="status(row).tag">{{ status(row).label }}</span></td>
      </tr>
      <tr v-if="rows.length === 0">
        <td colspan="6" class="empty">暂无库存</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.stock-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th,
td {
  padding: 12px 14px;
  border-bottom: 1px solid #edf0f4;
  text-align: left;
  vertical-align: middle;
}
th {
  color: var(--muted, #637083);
  font-size: 12px;
  font-weight: 700;
  background: #fafbfc;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 700;
}
.tag.ok {
  color: var(--green, #117a55);
  background: #e8f6ef;
}
.tag.warn {
  color: var(--amber, #b7791f);
  background: #fff6df;
}
.tag.danger {
  color: var(--red, #b42318);
  background: #fff0ee;
}
.empty {
  text-align: center;
  color: var(--muted, #637083);
  padding: 24px;
}
</style>
