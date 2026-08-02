import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import MovementsView from './MovementsView.vue'

const movementsMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerInventoryMovements: (...args: unknown[]) => movementsMock(...args),
}))

const MOVEMENTS = [
  {
    movement_uid: 'mv_000000000001',
    operation_type: 'purchase_in',
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity_delta: 20,
    new_quantity: 24,
    unit: '件',
    total_amount: 80,
    counterparty_name: '供应商甲',
    created_at: '2026-08-02T10:00:00',
  },
]

describe('MovementsView', () => {
  beforeEach(() => {
    movementsMock.mockReset()
  })

  it('loads movements on mount with no filters and renders the table', async () => {
    movementsMock.mockResolvedValue(MOVEMENTS)
    const wrapper = mount(MovementsView)
    await flushPromises()

    expect(movementsMock).toHaveBeenCalledWith({})
    expect(wrapper.text()).toContain('usb_cable_1m')
  })

  it('re-fetches when the operation type filter changes', async () => {
    movementsMock.mockResolvedValue(MOVEMENTS)
    const wrapper = mount(MovementsView)
    await flushPromises()

    movementsMock.mockClear()
    await wrapper.find('select[data-test="filter-operation"]').setValue('sales_out')
    await flushPromises()

    expect(movementsMock).toHaveBeenCalledTimes(1)
    expect(movementsMock).toHaveBeenCalledWith(
      expect.objectContaining({ operationType: 'sales_out' }),
    )
  })

  it('includes date_from when a from date is set', async () => {
    movementsMock.mockResolvedValue(MOVEMENTS)
    const wrapper = mount(MovementsView)
    await flushPromises()

    movementsMock.mockClear()
    await wrapper.find('input[data-test="date-from"]').setValue('2026-08-01')
    await flushPromises()

    expect(movementsMock).toHaveBeenCalledWith(
      expect.objectContaining({ dateFrom: '2026-08-01' }),
    )
  })

  it('includes date_to when a to date is set', async () => {
    movementsMock.mockResolvedValue(MOVEMENTS)
    const wrapper = mount(MovementsView)
    await flushPromises()

    movementsMock.mockClear()
    await wrapper.find('input[data-test="date-to"]').setValue('2026-08-02')
    await flushPromises()

    expect(movementsMock).toHaveBeenCalledWith(
      expect.objectContaining({ dateTo: '2026-08-02' }),
    )
  })
})
