import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ApiError } from '../api/client'
import SummaryView from './SummaryView.vue'

const summaryMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerSummary: (...args: unknown[]) => summaryMock(...args),
}))

const SUMMARY = {
  status: 'ok',
  date_from: null,
  date_to: null,
  sales_amount: 1280,
  purchase_amount: 600,
  net_cash_flow: 680,
  purchase_count: 3,
  sales_count: 5,
  movement_count: 8,
  product_count: 4,
  stock_location_count: 6,
  current_stock_quantity: 42,
  estimated_inventory_value: 2100,
  valuation_method: 'weighted_average_purchase_cost',
  low_stock_items: [{ product_uid: 'usb_cable_1m', quantity: 2, unit: '根' }],
  top_products_by_sales: [
    { product_uid: 'usb_cable_1m', sales_amount: 640, sales_quantity: 16 },
  ],
}

describe('SummaryView', () => {
  beforeEach(() => {
    summaryMock.mockReset()
  })

  it('loads the summary on mount and renders the headline metrics', async () => {
    summaryMock.mockResolvedValue(SUMMARY)
    const wrapper = mount(SummaryView)

    expect(summaryMock).toHaveBeenCalledTimes(1)
    await flushPromises()

    expect(wrapper.text()).toContain('1280')
    expect(wrapper.text()).toContain('600')
    expect(wrapper.text()).toContain('680')
    expect(wrapper.find('[data-test="summary"]').exists()).toBe(true)
  })

  it('renders low stock items and top products', async () => {
    summaryMock.mockResolvedValue(SUMMARY)
    const wrapper = mount(SummaryView)
    await flushPromises()

    expect(wrapper.text()).toContain('usb_cable_1m')
    expect(wrapper.find('[data-test="low-stock"]').text()).toContain('usb_cable_1m')
    expect(wrapper.find('[data-test="top-products"]').text()).toContain('usb_cable_1m')
  })

  it('emits logged-out when the backend rejects with 401', async () => {
    summaryMock.mockRejectedValue(new ApiError(401, 'unauthorized'))
    const wrapper = mount(SummaryView)
    await flushPromises()

    expect(wrapper.emitted('logged-out')).toBeTruthy()
  })
})
