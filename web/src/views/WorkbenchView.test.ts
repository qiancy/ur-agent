import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkbenchView from './WorkbenchView.vue'

const workbenchMock = vi.fn()
const purchaseMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerWorkbench: (...args: unknown[]) => workbenchMock(...args),
  sellerPurchaseIn: (...args: unknown[]) => purchaseMock(...args),
  sellerSalesOut: vi.fn(),
  sellerChat: vi.fn(),
}))

const SUMMARY = {
  status: 'ok',
  date_from: null,
  date_to: null,
  sales_amount: 12840,
  purchase_amount: 7260,
  net_cash_flow: 5580,
  purchase_count: 6,
  sales_count: 18,
  movement_count: 24,
  product_count: 42,
  stock_location_count: 128,
  current_stock_quantity: 1300,
  estimated_inventory_value: 48930,
  valuation_method: 'weighted_average_purchase_cost',
  low_stock_items: [{ product_uid: 'usb_cable_1m', quantity: 4, unit: '件' }],
  top_products_by_sales: [],
}

const STOCK = [
  {
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity: 4,
    unit: '件',
  },
]

describe('WorkbenchView', () => {
  beforeEach(() => {
    workbenchMock.mockReset()
    purchaseMock.mockReset()
  })

  it('loads aggregate workbench data on mount and renders metrics + stock', async () => {
    workbenchMock.mockResolvedValue({
      status: 'ok',
      summary: SUMMARY,
      stock: STOCK,
      movements: [],
    })
    const wrapper = mount(WorkbenchView)
    await flushPromises()

    expect(workbenchMock).toHaveBeenCalledTimes(1)
    expect(workbenchMock).toHaveBeenCalledWith({ movementsLimit: 10 })
    expect(wrapper.text()).toContain('12840')
    expect(wrapper.text()).toContain('usb_cable_1m')
  })

  it('opens the entry modal when the purchase button is clicked', async () => {
    workbenchMock.mockResolvedValue({
      status: 'ok',
      summary: SUMMARY,
      stock: STOCK,
      movements: [],
    })
    const wrapper = mount(WorkbenchView)
    await flushPromises()

    await wrapper.find('button[data-test="btn-purchase"]').trigger('click')
    expect(wrapper.find('[data-test="product_uid"]').exists()).toBe(true)
  })

  it('closes the modal without submitting when cancel is clicked', async () => {
    workbenchMock.mockResolvedValue({
      status: 'ok',
      summary: SUMMARY,
      stock: STOCK,
      movements: [],
    })
    const wrapper = mount(WorkbenchView)
    await flushPromises()

    await wrapper.find('button[data-test="btn-purchase"]').trigger('click')
    await wrapper.find('button[data-test="cancel"]').trigger('click')
    expect(wrapper.find('[data-test="product_uid"]').exists()).toBe(false)
  })

  it('reloads aggregate workbench data after a successful entry submit', async () => {
    workbenchMock.mockResolvedValue({
      status: 'ok',
      summary: SUMMARY,
      stock: STOCK,
      movements: [],
    })
    const wrapper = mount(WorkbenchView)
    await flushPromises()

    workbenchMock.mockClear()
    purchaseMock.mockResolvedValue({ status: 'ok', new_quantity: 24 })

    await wrapper.find('button[data-test="btn-purchase"]').trigger('click')
    await wrapper.find('[data-test="product_uid"]').setValue('usb_cable_1m')
    await wrapper.find('[data-test="warehouse_code"]').setValue('WH-A')
    await wrapper.find('[data-test="location_path"]').setValue('A-02-01')
    await wrapper.find('[data-test="quantity"]').setValue('20')
    await wrapper.find('[data-test="unit"]').setValue('件')
    await wrapper.find('[data-test="total_amount"]').setValue('80')
    await wrapper.find('[data-test="counterparty_name"]').setValue('供应商甲')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(purchaseMock).toHaveBeenCalledTimes(1)
    expect(workbenchMock).toHaveBeenCalledWith({ movementsLimit: 10 })
    expect(wrapper.find('[data-test="product_uid"]').exists()).toBe(false)
  })
})
