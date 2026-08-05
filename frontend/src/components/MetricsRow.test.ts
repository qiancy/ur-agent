import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MetricsRow from './MetricsRow.vue'

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

describe('MetricsRow', () => {
  it('renders the five headline metrics', () => {
    const wrapper = mount(MetricsRow, { props: { summary: SUMMARY } })

    expect(wrapper.find('[data-test="metric-sales"]').text()).toBe('12840')
    expect(wrapper.find('[data-test="metric-purchase"]').text()).toBe('7260')
    expect(wrapper.find('[data-test="metric-cashflow"]').text()).toBe('5580')
    expect(wrapper.find('[data-test="metric-inventory"]').text()).toBe('48930')
    expect(wrapper.find('[data-test="metric-low-stock"]').text()).toBe('1')
  })

  it('shows no DB id fields in rendered output', () => {
    const wrapper = mount(MetricsRow, { props: { summary: SUMMARY } })
    expect(wrapper.text()).not.toMatch(/[a-z]+_id/i)
  })
})
