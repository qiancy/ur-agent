<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { sellerPurchaseIn, sellerSalesOut } from '../api/seller'
import { listProducts, type SellerProduct } from '../api/products'

const props = defineProps<{
  mode: 'purchase_in' | 'sales_out'
}>()

const emit = defineEmits<{
  (e: 'submitted'): void
  (e: 'close'): void
}>()

const loading = ref(false)
const error = ref('')

const form = reactive({
  product_uid: '',
  warehouse_code: '',
  location_path: '',
  quantity: '',
  unit: '件',
  total_amount: '',
  counterparty_name: '',
})

const activeProducts = ref<SellerProduct[]>([])
const showOptions = ref(false)
const unknownConfirm = ref(false)

const title = computed(() =>
  props.mode === 'purchase_in' ? '入库' : '出库',
)

const productMatches = computed(() => {
  const query = form.product_uid.trim().toLowerCase()
  if (!query) return []
  return activeProducts.value.filter((p) =>
    p.product_uid.toLowerCase().includes(query),
  )
})

const needsUnknownConfirm = computed(
  () =>
    activeProducts.value.length > 0 &&
    !activeProducts.value.some(
      (p) => p.product_uid === form.product_uid.trim(),
    ) &&
    !unknownConfirm.value,
)

onMounted(async () => {
  try {
    activeProducts.value = (await listProducts()).filter(
      (p) => p.status === 'active',
    )
  } catch {
    activeProducts.value = []
  }
})

function onProductInput() {
  unknownConfirm.value = false
  showOptions.value = true
}

function pickProduct(uid: string) {
  form.product_uid = uid
  unknownConfirm.value = false
  showOptions.value = false
}

function validate(): string[] {
  const errors: string[] = []
  const quantity = Number(form.quantity)
  const amount = Number(form.total_amount)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    errors.push('数量必须大于 0')
  }
  if (!Number.isFinite(amount) || amount < 0) {
    errors.push('金额不能为负数')
  }
  if (!form.product_uid.trim()) errors.push('请填写商品编号')
  if (!form.warehouse_code.trim()) errors.push('请填写仓库编码')
  if (!form.location_path.trim()) errors.push('请填写库位')
  if (!form.counterparty_name.trim()) errors.push('请填写往来方')
  return errors
}

async function onSubmit() {
  error.value = ''
  const errors = validate()
  if (errors.length > 0) {
    error.value = errors.join('；')
    return
  }
  if (needsUnknownConfirm.value) {
    unknownConfirm.value = true
    return
  }
  await doSubmit()
}

async function confirmUnknownSubmit() {
  unknownConfirm.value = false
  await doSubmit()
}

async function doSubmit() {
  loading.value = true
  try {
    const body = {
      product_uid: form.product_uid.trim(),
      warehouse_code: form.warehouse_code.trim(),
      location_path: form.location_path.trim(),
      quantity: Number(form.quantity),
      unit: form.unit.trim() || '件',
      total_amount: Number(form.total_amount),
      counterparty_name: form.counterparty_name.trim(),
    }
    if (props.mode === 'purchase_in') {
      await sellerPurchaseIn(body)
    } else {
      await sellerSalesOut(body)
    }
    emit('submitted')
  } catch (e) {
    error.value = e instanceof Error ? e.message : `${title.value}失败，请重试`
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-mask" @click.self="emit('close')">
    <div class="modal" role="dialog" :aria-label="title">
      <div class="modal-head">
        <div class="modal-title">{{ title }}</div>
        <button class="close" type="button" data-test="close" @click="emit('close')">×</button>
      </div>
      <form class="modal-body" @submit.prevent="onSubmit">
        <label class="field">
          <span class="field-label">商品编号</span>
          <input
            v-model="form.product_uid"
            data-test="product_uid"
            type="text"
            placeholder="搜索选择或手动输入"
            autocomplete="off"
            @focus="showOptions = true"
            @input="onProductInput"
          />
          <ul v-if="showOptions && productMatches.length" class="product-options" data-test="product-options">
            <li v-for="p in productMatches" :key="p.product_uid">
              <button
                type="button"
                class="option"
                :data-test="`option-${p.product_uid}`"
                @mousedown.prevent="pickProduct(p.product_uid)"
                @click="pickProduct(p.product_uid)"
              >
                {{ p.product_uid }} · {{ p.unit }}
              </button>
            </li>
          </ul>
        </label>
        <label class="field">
          <span class="field-label">仓库编码</span>
          <input v-model="form.warehouse_code" data-test="warehouse_code" type="text" placeholder="WH-A" />
        </label>
        <label class="field">
          <span class="field-label">库位</span>
          <input v-model="form.location_path" data-test="location_path" type="text" placeholder="A-02-01" />
        </label>
        <div class="field-row">
          <label class="field">
            <span class="field-label">数量</span>
            <input v-model="form.quantity" data-test="quantity" type="number" min="0.01" step="any" />
          </label>
          <label class="field">
            <span class="field-label">单位</span>
            <input v-model="form.unit" data-test="unit" type="text" placeholder="件" />
          </label>
        </div>
        <label class="field">
          <span class="field-label">金额</span>
          <input v-model="form.total_amount" data-test="total_amount" type="number" min="0" step="any" />
        </label>
        <label class="field">
          <span class="field-label">往来方</span>
          <input v-model="form.counterparty_name" data-test="counterparty_name" type="text" />
        </label>
        <p v-if="error" class="form-error" data-test="form-error">{{ error }}</p>
        <div class="modal-actions">
          <button class="btn" type="button" data-test="cancel" @click="emit('close')">取消</button>
          <button class="btn primary" type="submit" :disabled="loading" data-test="submit">
            {{ loading ? '提交中…' : '确认' + title }}
          </button>
        </div>
      </form>

      <div v-if="unknownConfirm" class="confirm-mask" data-test="unknown-confirm" @click.self="unknownConfirm = false">
        <div class="confirm-box" role="dialog" aria-label="确认新增商品">
          <div class="confirm-head">
            <div class="confirm-title">确认新增商品</div>
          </div>
          <div class="confirm-body">
            <p class="confirm-text">该商品不存在，确认新增？</p>
            <div class="modal-actions">
              <button class="btn" type="button" data-test="cancel-unknown" @click="unknownConfirm = false">取消</button>
              <button class="btn primary" type="button" data-test="confirm-unknown" @click="confirmUnknownSubmit">确认</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
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
.product-options {
  margin: 0;
  padding: 4px;
  list-style: none;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  background: #ffffff;
  max-height: 180px;
  overflow-y: auto;
}
.product-options .option {
  display: block;
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  padding: 8px 10px;
  font-size: 13px;
  cursor: pointer;
  border-radius: 5px;
}
.product-options .option:hover {
  background: #f0f4f8;
}
.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(22, 32, 46, 0.35);
  display: grid;
  place-items: center;
  z-index: 120;
}
.confirm-box {
  width: 340px;
  max-width: 90vw;
  background: var(--panel, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--line, #d8dee8);
  box-shadow: 0 12px 40px rgba(22, 32, 46, 0.2);
}
.confirm-head {
  padding: 14px 18px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.confirm-title {
  font-size: 15px;
  font-weight: 750;
}
.confirm-body {
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
input {
  padding: 9px 11px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  font-size: 13px;
}
input:focus {
  outline: 2px solid var(--blue, #1d4f91);
  outline-offset: 1px;
}
.form-error {
  margin: 0;
  font-size: 12px;
  color: var(--red, #b42318);
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 7px;
  padding: 9px 14px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
