import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import EntryFormModal from './EntryFormModal.vue'

const purchaseMock = vi.fn()
const salesMock = vi.fn()
const productsMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerPurchaseIn: (...args: unknown[]) => purchaseMock(...args),
  sellerSalesOut: (...args: unknown[]) => salesMock(...args),
}))

vi.mock('../api/products', () => ({
  listProducts: (...args: unknown[]) => productsMock(...args),
}))

function fillForm(wrapper: ReturnType<typeof mount>) {
  return {
    product: wrapper.find('[data-test="product_uid"]'),
    warehouse: wrapper.find('[data-test="warehouse_code"]'),
    location: wrapper.find('[data-test="location_path"]'),
    quantity: wrapper.find('[data-test="quantity"]'),
    unit: wrapper.find('[data-test="unit"]'),
    amount: wrapper.find('[data-test="total_amount"]'),
    counterparty: wrapper.find('[data-test="counterparty_name"]'),
  }
}

async function fillAll(wrapper: ReturnType<typeof mount>, mode: 'purchase_in' | 'sales_out') {
  const f = fillForm(wrapper)
  await f.product.setValue('usb_cable_1m')
  await f.warehouse.setValue('WH-A')
  await f.location.setValue('A-02-01')
  await f.quantity.setValue('20')
  await f.unit.setValue('件')
  await f.amount.setValue('80')
  await f.counterparty.setValue(mode === 'purchase_in' ? '供应商甲' : '买家乙')
}

describe('EntryFormModal', () => {
  beforeEach(() => {
    purchaseMock.mockReset()
    salesMock.mockReset()
    productsMock.mockReset()
    productsMock.mockResolvedValue([])
  })

  it('renders purchase-in form with all business fields when mode is purchase_in', () => {
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    expect(wrapper.find('[data-test="product_uid"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="warehouse_code"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="location_path"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="quantity"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="total_amount"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="counterparty_name"]').exists()).toBe(true)
  })

  it('submits business fields only to sellerPurchaseIn and emits submitted', async () => {
    purchaseMock.mockResolvedValue({ status: 'ok', new_quantity: 24 })
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })

    await fillAll(wrapper, 'purchase_in')
    await wrapper.find('form').trigger('submit')

    expect(purchaseMock).toHaveBeenCalledTimes(1)
    expect(purchaseMock).toHaveBeenCalledWith({
      product_uid: 'usb_cable_1m',
      warehouse_code: 'WH-A',
      location_path: 'A-02-01',
      quantity: 20,
      unit: '件',
      total_amount: 80,
      counterparty_name: '供应商甲',
    })
    await flushPromises()
    expect(wrapper.emitted('submitted')).toBeTruthy()
  })

  it('submits to sellerSalesOut when mode is sales_out', async () => {
    salesMock.mockResolvedValue({ status: 'ok', new_quantity: 4 })
    const wrapper = mount(EntryFormModal, { props: { mode: 'sales_out' } })

    await fillAll(wrapper, 'sales_out')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(salesMock).toHaveBeenCalledTimes(1)
    expect(salesMock.mock.calls[0][0].counterparty_name).toBe('买家乙')
    expect(wrapper.emitted('submitted')).toBeTruthy()
  })

  it('rejects quantity <= 0 and total_amount < 0 before submitting', async () => {
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    const f = fillForm(wrapper)
    await f.quantity.setValue('0')
    await f.amount.setValue('-5')

    await wrapper.find('form').trigger('submit')

    expect(purchaseMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('数量必须大于 0')
    expect(wrapper.text()).toContain('金额不能为负数')
  })

  it('disables the submit button while loading (prevents double-click)', async () => {
    let resolveFetch: (v: unknown) => void = () => {}
    purchaseMock.mockImplementation(
      () => new Promise((resolve) => (resolveFetch = resolve)),
    )
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })

    await fillAll(wrapper, 'purchase_in')
    const submitBtn = wrapper.find('button[type="submit"]')
    await wrapper.find('form').trigger('submit')

    expect(submitBtn.attributes('disabled')).toBeDefined()

    resolveFetch({ status: 'ok' })
    await flushPromises()
  })

  it('shows the backend error text on failure and does not emit submitted', async () => {
    purchaseMock.mockRejectedValue(new Error('Insufficient stock: have 2, need 20'))
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })

    await fillAll(wrapper, 'purchase_in')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Insufficient stock')
    expect(wrapper.emitted('submitted')).toBeUndefined()
  })

  it('does not submit any DB id fields', async () => {
    purchaseMock.mockResolvedValue({ status: 'ok', new_quantity: 24 })
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })

    await fillAll(wrapper, 'purchase_in')
    await wrapper.find('form').trigger('submit')

    const body = purchaseMock.mock.calls[0][0]
    const keys = Object.keys(body)
    for (const key of keys) {
      expect(key).not.toBe('id')
      expect(key).not.toBe('pid')
      expect(key).not.toBe('oid')
      expect(key.endsWith('_id')).toBe(false)
    }
  })

  it('filters searchable product options from active products', async () => {
    productsMock.mockResolvedValue([
      { product_uid: 'SKU-001', unit: '个', status: 'active', stock_total: 5, stock_location_count: 1, description: null },
      { product_uid: 'SKU-002', unit: '盒', status: 'active', stock_total: 3, stock_location_count: 1, description: null },
      { product_uid: 'SKU-OLD', unit: '个', status: 'inactive', stock_total: 0, stock_location_count: 0, description: null },
    ])
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    await flushPromises()

    const input = wrapper.find('[data-test="product_uid"]')
    await input.trigger('focus')
    await input.setValue('SKU-00')

    const options = wrapper.findAll('[data-test^="option-"]')
    expect(options).toHaveLength(2)
    expect(wrapper.find('[data-test="option-SKU-001"]').text()).toContain('SKU-001')
    expect(wrapper.find('[data-test="option-SKU-OLD"]').exists()).toBe(false)
  })

  it('picks a product from the options and uses its uid', async () => {
    productsMock.mockResolvedValue([
      { product_uid: 'SKU-001', unit: '个', status: 'active', stock_total: 5, stock_location_count: 1, description: null },
      { product_uid: 'SKU-002', unit: '盒', status: 'active', stock_total: 3, stock_location_count: 1, description: null },
    ])
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    await flushPromises()

    const input = wrapper.find('[data-test="product_uid"]')
    await input.trigger('focus')
    await input.setValue('SKU-00')
    await wrapper.find('[data-test="option-SKU-002"]').trigger('click')

    expect((input.element as HTMLInputElement).value).toBe('SKU-002')
    expect(wrapper.find('[data-test="product-options"]').exists()).toBe(false)
  })

  it('asks for a second confirmation when the product does not exist', async () => {
    productsMock.mockResolvedValue([
      { product_uid: 'SKU-001', unit: '个', status: 'active', stock_total: 5, stock_location_count: 1, description: null },
    ])
    purchaseMock.mockResolvedValue({ status: 'ok', new_quantity: 20 })
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    await flushPromises()

    await fillAll(wrapper, 'purchase_in')
    await wrapper.find('form').trigger('submit')

    expect(purchaseMock).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="unknown-confirm"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('该商品不存在，确认新增？')

    await wrapper.find('[data-test="confirm-unknown"]').trigger('click')
    await flushPromises()

    expect(purchaseMock).toHaveBeenCalledTimes(1)
    expect(wrapper.emitted('submitted')).toBeTruthy()
  })

  it('does not submit when the unknown-product confirmation is cancelled', async () => {
    productsMock.mockResolvedValue([
      { product_uid: 'SKU-001', unit: '个', status: 'active', stock_total: 5, stock_location_count: 1, description: null },
    ])
    const wrapper = mount(EntryFormModal, { props: { mode: 'purchase_in' } })
    await flushPromises()

    await fillAll(wrapper, 'purchase_in')
    await wrapper.find('form').trigger('submit')

    await wrapper.find('[data-test="cancel-unknown"]').trigger('click')

    expect(purchaseMock).not.toHaveBeenCalled()
    expect(wrapper.emitted('submitted')).toBeUndefined()
  })
})
