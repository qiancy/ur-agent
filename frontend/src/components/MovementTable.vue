<script setup lang="ts">
import type { SellerMovement } from '../api/seller'

defineProps<{
  rows: SellerMovement[]
}>()

function deltaText(row: SellerMovement): string {
  const delta = Number(row.quantity_delta)
  return delta >= 0 ? `+${delta}` : `${delta}`
}
</script>

<template>
  <table class="movement-table">
    <thead>
      <tr>
        <th>时间</th>
        <th>类型</th>
        <th>商品</th>
        <th>仓库/库位</th>
        <th class="num">变动</th>
        <th class="num">结存</th>
        <th class="num">金额</th>
        <th>往来方</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.movement_uid">
        <td>{{ row.created_at?.slice(0, 19).replace('T', ' ') }}</td>
        <td>
          <span
            class="tag"
            :class="row.operation_type === 'purchase_in' ? 'movement-purchase' : 'movement-sales'"
          >
            {{ row.operation_type === 'purchase_in' ? '入库' : '出库' }}
          </span>
        </td>
        <td>{{ row.product_uid }}</td>
        <td>{{ row.warehouse_code }} · {{ row.location_path }}</td>
        <td class="num">{{ deltaText(row) }}</td>
        <td class="num">{{ row.new_quantity }}</td>
        <td class="num">{{ row.total_amount }}</td>
        <td>{{ row.counterparty_name }}</td>
      </tr>
      <tr v-if="rows.length === 0">
        <td colspan="8" class="empty">暂无流水</td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.movement-table {
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
.movement-purchase {
  color: var(--green, #117a55);
  background: #e8f6ef;
}
.movement-sales {
  color: var(--red, #b42318);
  background: #fff0ee;
}
.empty {
  text-align: center;
  color: var(--muted, #637083);
  padding: 24px;
}
</style>
