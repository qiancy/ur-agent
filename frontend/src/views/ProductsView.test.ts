import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ApiError } from '../api/client'
import ProductsView from './ProductsView.vue'

const listMock = vi.fn()
const createMock = vi.fn()
const statusMock = vi.fn()

vi.mock('../api/products', () => ({
  listProducts: (...args: unknown[]) => listMock(...args),
  createProduct: (...args: unknown[]) => createMock(...args),
  setProductStatus: (...args: unknown[]) => statusMock(...args),
}))

const PRODUCTS = [
  {
    product_uid: 'SKU-001',
    unit: '个',
    status: 'active',
    stock_total: 120,
    stock_location_count: 2,
    description: '热销款',
  },
  {
    product_uid: 'SKU-002',
    unit: '盒',
    status: 'inactive',
    stock_total: 0,
    stock_location_count: 0,
    description: null,
  },
]

describe('ProductsView', () => {
  beforeEach(() => {
    listMock.mockReset()
    createMock.mockReset()
    statusMock.mockReset()
  })

  it('loads and renders the product list with all columns', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    const wrapper = mount(ProductsView)
    await flushPromises()

    expect(listMock).toHaveBeenCalledTimes(1)
    const rows = wrapper.findAll('[data-test="product-row"]')
    expect(rows).toHaveLength(2)
    expect(wrapper.text()).toContain('SKU-001')
    expect(wrapper.text()).toContain('个')
    expect(wrapper.text()).toContain('120')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('热销款')
    expect(wrapper.text()).toContain('已停用')
  })

  it('adds a new product and reloads the list', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    createMock.mockResolvedValue({
      product_uid: 'SKU-003',
      unit: '个',
      status: 'active',
      stock_total: 0,
      stock_location_count: 0,
      description: null,
    })
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.find('[data-test="btn-add"]').trigger('click')
    await wrapper.find('[data-test="add-product_uid"]').setValue('SKU-003')
    await wrapper.find('[data-test="add-unit"]').setValue('个')
    await wrapper.find('[data-test="add-description"]').setValue('新品')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createMock).toHaveBeenCalledWith({
      product_uid: 'SKU-003',
      unit: '个',
      description: '新品',
    })
    expect(listMock).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[data-test="add-product_uid"]').exists()).toBe(false)
  })

  it('omits description from the add request when left empty', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    createMock.mockResolvedValue({
      product_uid: 'SKU-003',
      unit: '个',
      status: 'active',
      stock_total: 0,
      stock_location_count: 0,
      description: null,
    })
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.find('[data-test="btn-add"]').trigger('click')
    await wrapper.find('[data-test="add-product_uid"]').setValue('SKU-003')
    await wrapper.find('[data-test="add-unit"]').setValue('个')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createMock).toHaveBeenCalledWith({
      product_uid: 'SKU-003',
      unit: '个',
      description: undefined,
    })
  })

  it('validates product_uid and unit before submitting the add form', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.find('[data-test="btn-add"]').trigger('click')
    await wrapper.find('[data-test="add-unit"]').setValue('个')
    await wrapper.find('form').trigger('submit')

    expect(createMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('请填写商品编号')

    await wrapper.find('[data-test="add-product_uid"]').setValue('SKU-003')
    await wrapper.find('[data-test="add-unit"]').setValue('')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.text()).toContain('请填写单位')
  })

  it('deactivates an active product only after confirming', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    statusMock.mockResolvedValue({
      product_uid: 'SKU-001',
      unit: '个',
      status: 'inactive',
    })
    const wrapper = mount(ProductsView)
    await flushPromises()

    const toggleButtons = wrapper.findAll('[data-test="btn-toggle"]')
    await toggleButtons[0].trigger('click')

    expect(statusMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('历史流水保留')
    expect(wrapper.text()).toContain('SKU-001')

    await wrapper.find('[data-test="confirm-toggle"]').trigger('click')
    await flushPromises()

    expect(statusMock).toHaveBeenCalledWith('SKU-001', 'inactive')
    expect(listMock).toHaveBeenCalledTimes(2)
  })

  it('cancels deactivation without calling the API', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.findAll('[data-test="btn-toggle"]')[0].trigger('click')
    await wrapper.find('[data-test="cancel-toggle"]').trigger('click')

    expect(statusMock).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="toggle-confirm-text"]').exists()).toBe(false)
  })

  it('reactivates an inactive product directly without confirmation', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    statusMock.mockResolvedValue({
      product_uid: 'SKU-002',
      unit: '盒',
      status: 'active',
    })
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.findAll('[data-test="btn-toggle"]')[1].trigger('click')
    await flushPromises()

    expect(statusMock).toHaveBeenCalledWith('SKU-002', 'active')
    expect(wrapper.find('[data-test="toggle-confirm-text"]').exists()).toBe(false)
  })

  it('filters the list by status', async () => {
    listMock.mockResolvedValue(PRODUCTS)
    const wrapper = mount(ProductsView)
    await flushPromises()

    await wrapper.find('[data-test="status-filter"]').setValue('inactive')
    await flushPromises()

    const rows = wrapper.findAll('[data-test="product-row"]')
    expect(rows).toHaveLength(1)
    expect(rows[0].text()).toContain('SKU-002')
  })

  it('emits logged-out when the backend rejects with 401', async () => {
    listMock.mockRejectedValue(new ApiError(401, 'unauthorized'))
    const wrapper = mount(ProductsView)
    await flushPromises()

    expect(wrapper.emitted('logged-out')).toBeTruthy()
  })
})
