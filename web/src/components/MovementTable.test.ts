import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MovementTable from './MovementTable.vue'

const ROWS: import('../api/seller').SellerMovement[] = [
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
  {
    movement_uid: 'mv_000000000002',
    operation_type: 'sales_out',
    product_uid: 'charger_20w',
    warehouse_code: 'WH-A',
    location_path: 'A-03-02',
    quantity_delta: -2,
    new_quantity: 8,
    unit: '件',
    total_amount: 60,
    counterparty_name: '买家乙',
    created_at: '2026-08-02T11:30:00',
  },
]

describe('MovementTable', () => {
  it('renders each movement with operation type and direction', () => {
    const wrapper = mount(MovementTable, { props: { rows: ROWS } })

    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    expect(wrapper.text()).toContain('入库')
    expect(wrapper.text()).toContain('出库')
    expect(wrapper.find('.movement-purchase').exists()).toBe(true)
    expect(wrapper.find('.movement-sales').exists()).toBe(true)
  })

  it('shows quantity delta with sign', () => {
    const wrapper = mount(MovementTable, { props: { rows: ROWS } })
    expect(wrapper.text()).toContain('+20')
    expect(wrapper.text()).toContain('-2')
  })

  it('does not render DB id fields', () => {
    const wrapper = mount(MovementTable, { props: { rows: ROWS } })
    expect(wrapper.text()).not.toMatch(/\b(id|pid|oid)\b/i)
  })

  it('shows an empty message when there are no rows', () => {
    const wrapper = mount(MovementTable, { props: { rows: [] } })
    expect(wrapper.text()).toContain('暂无流水')
  })
})
