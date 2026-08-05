import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import StockView from './StockView.vue'

const stockMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerStock: (...args: unknown[]) => stockMock(...args),
}))

const STOCK = [
  {
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity: 4,
    unit: '件',
  },
]

describe('StockView', () => {
  beforeEach(() => {
    stockMock.mockReset()
  })

  it('loads full stock on mount and renders the table', async () => {
    stockMock.mockResolvedValue(STOCK)
    const wrapper = mount(StockView)
    await flushPromises()

    expect(stockMock).toHaveBeenCalledWith()
    expect(wrapper.text()).toContain('usb_cable_1m')
    expect(wrapper.find('tbody tr').exists()).toBe(true)
  })

  it('refreshes when the refresh button is clicked', async () => {
    stockMock.mockResolvedValue(STOCK)
    const wrapper = mount(StockView)
    await flushPromises()

    stockMock.mockClear()
    await wrapper.find('button[data-test="btn-refresh"]').trigger('click')
    await flushPromises()
    expect(stockMock).toHaveBeenCalledTimes(1)
  })

  it('filters stock by product uid when the filter is applied', async () => {
    stockMock.mockResolvedValue(STOCK)
    const wrapper = mount(StockView)
    await flushPromises()

    stockMock.mockClear()
    await wrapper.find('input[data-test="filter-product"]').setValue('usb_cable_1m')
    await wrapper.find('button[data-test="btn-filter"]').trigger('click')
    await flushPromises()

    expect(stockMock).toHaveBeenCalledWith('usb_cable_1m')
  })

  it('clears the product filter and reloads the full stock', async () => {
    stockMock.mockResolvedValue(STOCK)
    const wrapper = mount(StockView)
    await flushPromises()

    stockMock.mockClear()
    await wrapper.find('input[data-test="filter-product"]').setValue('usb_cable_1m')
    await wrapper.find('button[data-test="btn-filter"]').trigger('click')
    await flushPromises()

    stockMock.mockClear()
    await wrapper.find('input[data-test="filter-product"]').setValue('')
    await wrapper.find('button[data-test="btn-filter"]').trigger('click')
    await flushPromises()

    expect(stockMock).toHaveBeenCalledWith()
  })
})
