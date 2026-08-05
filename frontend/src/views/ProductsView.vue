<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ApiError } from '../api/client'
import {
  createProduct,
  listProducts,
  setProductStatus,
  type ProductStatus,
  type SellerProduct,
} from '../api/products'

const emit = defineEmits<{ (e: 'logged-out'): void }>()

const products = ref<SellerProduct[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref<'all' | ProductStatus>('all')

const showAdd = ref(false)
const adding = ref(false)
const addError = ref('')
const addForm = reactive({ product_uid: '', unit: '', description: '' })

const confirmProduct = ref<SellerProduct | null>(null)
const toggling = ref(false)

const visible = computed(() => {
  if (statusFilter.value === 'all') return products.value
  return products.value.filter((p) => p.status === statusFilter.value)
})

function handleError(e: unknown): boolean {
  if (e instanceof ApiError && e.status === 401) {
    emit('logged-out')
    return true
  }
  return false
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    products.value = await listProducts()
  } catch (e) {
    if (!handleError(e)) {
      error.value = e instanceof Error ? e.message : '商品列表加载失败'
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)

function resetAddForm() {
  addForm.product_uid = ''
  addForm.unit = ''
  addForm.description = ''
}

async function onAdd() {
  addError.value = ''
  const uid = addForm.product_uid.trim()
  const unit = addForm.unit.trim()
  if (!uid) {
    addError.value = '请填写商品编号'
    return
  }
  if (!unit) {
    addError.value = '请填写单位'
    return
  }
  adding.value = true
  try {
    await createProduct({
      product_uid: uid,
      unit,
      description: addForm.description.trim() || undefined,
    })
    showAdd.value = false
    resetAddForm()
    await load()
  } catch (e) {
    if (handleError(e)) return
    addError.value = e instanceof Error ? e.message : '新增商品失败'
  } finally {
    adding.value = false
  }
}

function requestToggle(p: SellerProduct) {
  if (p.status === 'inactive') {
    void applyStatus(p, 'active')
  } else {
    confirmProduct.value = p
  }
}

async function confirmToggle() {
  const p = confirmProduct.value
  confirmProduct.value = null
  if (p) await applyStatus(p, 'inactive')
}

async function applyStatus(p: SellerProduct, status: ProductStatus) {
  toggling.value = true
  try {
    await setProductStatus(p.product_uid, status)
    await load()
  } catch (e) {
    if (!handleError(e)) {
      error.value = e instanceof Error ? e.message : '操作失败'
    }
  } finally {
    toggling.value = false
  }
}
</script>

<template>
  <section class="products-view" data-test="products-view">
    <div class="topbar">
      <div>
        <h1>商品管理</h1>
        <div class="status">{{ products.length }} 个商品</div>
      </div>
      <button class="btn primary" type="button" data-test="btn-add" @click="showAdd = true">
        新增商品
      </button>
    </div>

    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">全部商品</div>
        <div class="filters">
          <select v-model="statusFilter" class="status-select" data-test="status-filter">
            <option value="all">全部</option>
            <option value="active">正常</option>
            <option value="inactive">已停用</option>
          </select>
          <span class="chip">{{ visible.length }} 项</span>
        </div>
      </div>

      <p v-if="loading" class="hint">加载中…</p>
      <p v-else-if="error" class="form-error" data-test="error">{{ error }}</p>
      <table v-else class="products-table" data-test="products-table">
        <thead>
          <tr>
            <th>商品编号</th>
            <th>单位</th>
            <th>状态</th>
            <th class="num">库存总数</th>
            <th class="num">库位数</th>
            <th>描述</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in visible" :key="p.product_uid" data-test="product-row">
            <td>{{ p.product_uid }}</td>
            <td>{{ p.unit }}</td>
            <td>
              <span class="tag" :class="p.status === 'active' ? 'ok' : 'off'">
                {{ p.status === 'active' ? '正常' : '已停用' }}
              </span>
            </td>
            <td class="num">{{ p.stock_total }}</td>
            <td class="num">{{ p.stock_location_count }}</td>
            <td class="desc">{{ p.description ?? '—' }}</td>
            <td class="ops">
              <button
                class="btn small"
                type="button"
                data-test="btn-toggle"
                :disabled="toggling"
                @click="requestToggle(p)"
              >
                {{ p.status === 'active' ? '停用' : '重新启用' }}
              </button>
            </td>
          </tr>
          <tr v-if="visible.length === 0">
            <td colspan="7" class="empty">暂无商品</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showAdd" class="modal-mask" @click.self="showAdd = false">
      <div class="modal" role="dialog" aria-label="新增商品">
        <div class="modal-head">
          <div class="modal-title">新增商品</div>
          <button class="close" type="button" data-test="close-add" @click="showAdd = false">×</button>
        </div>
        <form class="modal-body" @submit.prevent="onAdd">
          <label class="field">
            <span class="field-label">商品编号</span>
            <input v-model="addForm.product_uid" data-test="add-product_uid" type="text" placeholder="SKU-003" />
          </label>
          <label class="field">
            <span class="field-label">单位</span>
            <input v-model="addForm.unit" data-test="add-unit" type="text" placeholder="个" />
          </label>
          <label class="field">
            <span class="field-label">描述（可选）</span>
            <input v-model="addForm.description" data-test="add-description" type="text" />
          </label>
          <p v-if="addError" class="form-error" data-test="add-error">{{ addError }}</p>
          <div class="modal-actions">
            <button class="btn" type="button" data-test="cancel-add" @click="showAdd = false">取消</button>
            <button class="btn primary" type="submit" :disabled="adding" data-test="add-submit">
              {{ adding ? '提交中…' : '确认新增' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="confirmProduct" class="modal-mask" @click.self="confirmProduct = null">
      <div class="modal confirm" role="dialog" aria-label="停用确认">
        <div class="modal-head">
          <div class="modal-title">停用商品</div>
          <button class="close" type="button" data-test="close-toggle" @click="confirmProduct = null">×</button>
        </div>
        <div class="modal-body">
          <p class="confirm-text" data-test="toggle-confirm-text">
            停用后历史流水保留，确认停用商品「{{ confirmProduct.product_uid }}」？
          </p>
          <div class="modal-actions">
            <button class="btn" type="button" data-test="cancel-toggle" @click="confirmProduct = null">取消</button>
            <button class="btn primary" type="button" data-test="confirm-toggle" @click="confirmToggle">
              确认停用
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.products-view {
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
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn.small {
  padding: 6px 10px;
  font-size: 12px;
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
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
.filters {
  display: flex;
  gap: 8px;
  align-items: center;
}
.status-select {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  background: #fbfcfe;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
}
.products-table {
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
.desc {
  color: var(--muted, #637083);
  max-width: 240px;
}
.ops {
  text-align: right;
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
.tag.off {
  color: var(--muted, #637083);
  background: #eef1f5;
}
.hint {
  padding: 16px;
  color: var(--muted, #637083);
  font-size: 13px;
  margin: 0;
}
.form-error {
  padding: 16px;
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
.empty {
  text-align: center;
  color: var(--muted, #637083);
  padding: 24px;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(22, 32, 46, 0.45);
  display: grid;
  place-items: center;
  z-index: 100;
}
.modal {
  width: 420px;
  max-width: 92vw;
  background: var(--panel, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--line, #d8dee8);
  box-shadow: 0 12px 40px rgba(22, 32, 46, 0.2);
}
.modal.confirm {
  width: 380px;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.modal-title {
  font-size: 16px;
  font-weight: 750;
}
.close {
  border: 0;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--muted, #637083);
  cursor: pointer;
}
.modal-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.confirm-text {
  margin: 0;
  font-size: 14px;
  color: var(--ink, #17202a);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 12px;
  color: var(--muted, #637083);
}
.modal input {
  padding: 9px 11px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  font-size: 13px;
}
.modal input:focus {
  outline: 2px solid var(--blue, #1d4f91);
  outline-offset: 1px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
</style>
