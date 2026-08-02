import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StockTable from './StockTable.vue'

const ROWS = [
  {
    product_uid: 'phone_case_black',
    warehouse_code: 'WH-A',
    location_path: 'A-01-03',
    quantity: 42,
    unit: '件',
  },
  {
    product_uid: 'usb_cable_1m',
    warehouse_code: 'WH-A',
    location_path: 'A-02-01',
    quantity: 4,
    unit: '件',
  },
  {
    product_uid: 'screen_film_hd',
    warehouse_code: 'WH-B',
    location_path: 'B-01-08',
    quantity: 11,
    unit: '件',
  },
]

describe('StockTable', () => {
  it('renders each stock row with product, warehouse, location, qty, unit', () => {
    const wrapper = mount(StockTable, {
      props: { rows: ROWS, lowStockThreshold: 5 },
    })

    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
    expect(wrapper.text()).toContain('phone_case_black')
    expect(wrapper.text()).toContain('WH-A')
    expect(wrapper.text()).toContain('A-01-03')
    expect(wrapper.text()).toContain('42')
  })

  it('marks rows at or below the low-stock threshold as danger', () => {
    const wrapper = mount(StockTable, {
      props: { rows: ROWS, lowStockThreshold: 5 },
    })

    const dangerTags = wrapper.findAll('.tag.danger')
    expect(dangerTags).toHaveLength(1)
    expect(dangerTags[0].text()).toContain('低库存')
  })

  it('does not render DB id fields', () => {
    const wrapper = mount(StockTable, {
      props: { rows: ROWS, lowStockThreshold: 5 },
    })
    expect(wrapper.text()).not.toMatch(/[a-z]+_id/i)
  })

  it('shows an empty message when there are no rows', () => {
    const wrapper = mount(StockTable, {
      props: { rows: [], lowStockThreshold: 5 },
    })
    expect(wrapper.text()).toContain('暂无库存')
  })
})
