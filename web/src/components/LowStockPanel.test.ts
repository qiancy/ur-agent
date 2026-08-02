import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LowStockPanel from './LowStockPanel.vue'

const ITEMS = [
  { product_uid: 'usb_cable_1m', quantity: 4, unit: '件' },
  { product_uid: 'charger_20w', quantity: 2, unit: '件' },
]

const STOCK = [
  {
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity: 4,
    unit: '件',
  },
  {
    product_uid: 'charger_20w',
    warehouse_code: 'WH-A',
    location_path: 'A-03-02',
    quantity: 2,
    unit: '件',
  },
]

describe('LowStockPanel', () => {
  it('renders each low stock item with location and quantity', () => {
    const wrapper = mount(LowStockPanel, { props: { items: ITEMS, stock: STOCK } })

    expect(wrapper.findAll('.low-item')).toHaveLength(2)
    expect(wrapper.text()).toContain('usb_cable_1m')
    expect(wrapper.text()).toContain('WH-A · A-02-01')
    expect(wrapper.text()).toContain('4 件')
  })

  it('sorts items by quantity ascending (risk first)', () => {
    const wrapper = mount(LowStockPanel, { props: { items: ITEMS, stock: STOCK } })
    const quantities = wrapper.findAll('.low-item strong').map((n) => n.text())
    expect(quantities[0]).toContain('2')
    expect(quantities[1]).toContain('4')
  })

  it('shows a friendly message when there are no low stock items', () => {
    const wrapper = mount(LowStockPanel, { props: { items: [], stock: [] } })
    expect(wrapper.text()).toContain('暂无低库存')
  })
})
