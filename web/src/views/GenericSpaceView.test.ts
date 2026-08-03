import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ApiError } from '../api/client'
import GenericSpaceView from './GenericSpaceView.vue'

const overviewMock = vi.fn()
const resourcesMock = vi.fn()
const personsMock = vi.fn()
const transactionsMock = vi.fn()
const timelineMock = vi.fn()

vi.mock('../api/spaces', () => ({
  getSpaceOverview: (...args: unknown[]) => overviewMock(...args),
  getSpaceResources: (...args: unknown[]) => resourcesMock(...args),
  getSpacePersons: (...args: unknown[]) => personsMock(...args),
  getSpaceTransactions: (...args: unknown[]) => transactionsMock(...args),
  getSpaceTimeline: (...args: unknown[]) => timelineMock(...args),
}))

const OVERVIEW = {
  space: { ouid: 'zhangsan_family', name: '张三家庭', type: 'family', role: 'owner' },
  counts: { resources: 6, persons: 4, transactions: 3, recent_events: 2 },
  funds: 8500,
}

const RESOURCES = {
  grouped: {
    physical: [
      {
        name: '教材',
        type: 'physical',
        unit: '本',
        amount: 12,
        description: '小学五年级数学',
        locations: [
          { warehouse_code: 'WH1', location_path: 'A1', quantity: 12, unit: '本' },
          { warehouse_code: 'WH1', location_path: 'A2', quantity: 3, unit: '本' },
        ],
      },
    ],
    knowledge: [
      { name: '错题本', type: 'knowledge', unit: '份', amount: null, description: '张小宝错题整理' },
    ],
    financial: [],
    human: [],
  },
}

const PERSONS = [
  { name: '张三', puid: 'zhangsan', role: 'owner' },
  { name: '张小宝', puid: 'xiaobao', role: 'member' },
]

const TRANSACTIONS = [
  {
    transaction_uid: 'txn-0001',
    from_party_name: '张三',
    to_party_name: '书店',
    amount: 128,
    category: '教育支出',
    description: '购买教材',
    created_at: '2026-08-01T10:00:00',
  },
]

const TIMELINE = {
  events: [
    {
      seq: 1,
      campaign_code: 'family_learning',
      campaign_name: '家庭学习空间',
      title: '每日学习要求',
      description: '完成数学口算 20 题',
      payload: {
        info_flow: '通知下发',
        logistics_flow: '教材由书店送达',
        people_flow: '张小宝',
        risk: '注意力不集中',
      },
    },
  ],
}

const EMPTY_TIMELINE = { events: [] }

function mockAll() {
  overviewMock.mockResolvedValue(OVERVIEW)
  resourcesMock.mockResolvedValue(RESOURCES)
  personsMock.mockResolvedValue(PERSONS)
  transactionsMock.mockResolvedValue(TRANSACTIONS)
  timelineMock.mockResolvedValue(TIMELINE)
}

describe('GenericSpaceView', () => {
  beforeEach(() => {
    overviewMock.mockReset()
    resourcesMock.mockReset()
    personsMock.mockReset()
    transactionsMock.mockReset()
    timelineMock.mockReset()
  })

  it('loads all five data sources on mount and renders the overview block', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(overviewMock).toHaveBeenCalledTimes(1)
    expect(resourcesMock).toHaveBeenCalledTimes(1)
    expect(personsMock).toHaveBeenCalledTimes(1)
    expect(transactionsMock).toHaveBeenCalledTimes(1)
    expect(timelineMock).toHaveBeenCalledTimes(1)

    expect(wrapper.find('[data-test="ov-name"]').text()).toContain('张三家庭')
    expect(wrapper.find('[data-test="ov-type"]').text()).toContain('family')
    expect(wrapper.find('[data-test="ov-role"]').text()).toContain('owner')
    expect(wrapper.find('[data-test="ov-resources"]').text()).toContain('6')
    expect(wrapper.find('[data-test="ov-persons"]').text()).toContain('4')
    expect(wrapper.find('[data-test="ov-transactions"]').text()).toContain('3')
    expect(wrapper.find('[data-test="ov-events"]').text()).toContain('2')
    expect(wrapper.find('[data-test="ov-funds"]').text()).toContain('8500')
  })

  it('renders resource groups and expands physical locations on demand', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(wrapper.find('[data-test="group-physical"]').text()).toContain('教材')
    expect(wrapper.find('[data-test="group-knowledge"]').text()).toContain('错题本')
    expect(wrapper.find('[data-test="locations-table"]').exists()).toBe(false)

    await wrapper.find('[data-test="toggle-locations-教材"]').trigger('click')

    const table = wrapper.find('[data-test="locations-table"]')
    expect(table.exists()).toBe(true)
    const rows = wrapper.findAll('[data-test="location-row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('WH1')
    expect(rows[0].text()).toContain('A1')
    expect(rows[0].text()).toContain('12')
  })

  it('renders the persons observation block', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    const rows = wrapper.findAll('[data-test="person-row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('zhangsan')
    expect(rows[0].text()).toContain('owner')
  })

  it('renders the timeline events with their flow dimensions', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    const events = wrapper.findAll('[data-test="event-row"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('每日学习要求')
    expect(events[0].text()).toContain('家庭学习空间')
    expect(wrapper.find('[data-test="dim-info"]').text()).toContain('通知下发')
    expect(wrapper.find('[data-test="dim-logistics"]').text()).toContain('教材由书店送达')
    expect(wrapper.find('[data-test="dim-people"]').text()).toContain('张小宝')
    expect(wrapper.find('[data-test="dim-risk"]').text()).toContain('注意力不集中')
  })

  it('shows an empty state when there are no timeline events', async () => {
    overviewMock.mockResolvedValue(OVERVIEW)
    resourcesMock.mockResolvedValue(RESOURCES)
    personsMock.mockResolvedValue(PERSONS)
    transactionsMock.mockResolvedValue(TRANSACTIONS)
    timelineMock.mockResolvedValue(EMPTY_TIMELINE)
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(wrapper.find('[data-test="event-row"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="timeline-empty"]').text()).toContain('暂无事件')
  })

  it('renders the multi-dimensional flows including funds from transactions only', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(wrapper.find('[data-test="flow-info"]').text()).toContain('错题本')
    expect(wrapper.find('[data-test="flow-logistics"]').text()).toContain('教材')
    expect(wrapper.find('[data-test="flow-people"]').text()).toContain('张小宝')
    expect(wrapper.find('[data-test="flow-people"]').text()).toContain('张三')

    const funds = wrapper.find('[data-test="flow-funds"]')
    expect(funds.find('[data-test="funds-total"]').text()).toContain('8500')
    const txRows = wrapper.findAll('[data-test="tx-row"]')
    expect(txRows).toHaveLength(1)
    expect(txRows[0].text()).toContain('张三')
    expect(txRows[0].text()).toContain('书店')
    expect(txRows[0].text()).toContain('128')
    expect(txRows[0].text()).toContain('教育支出')
  })

  it('shows an empty funds state when there are no transactions', async () => {
    overviewMock.mockResolvedValue(OVERVIEW)
    resourcesMock.mockResolvedValue(RESOURCES)
    personsMock.mockResolvedValue(PERSONS)
    transactionsMock.mockResolvedValue([])
    timelineMock.mockResolvedValue(TIMELINE)
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(wrapper.findAll('[data-test="tx-row"]')).toHaveLength(0)
    expect(wrapper.find('[data-test="flow-funds"]').text()).toContain('暂无资金流水')
  })

  it('refreshes all data when the refresh button is clicked', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    overviewMock.mockClear()
    await wrapper.find('[data-test="btn-refresh"]').trigger('click')
    await flushPromises()

    expect(overviewMock).toHaveBeenCalledTimes(1)
  })

  it('emits logged-out when the backend rejects with 401', async () => {
    overviewMock.mockRejectedValue(new ApiError(401, 'unauthorized'))
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()

    expect(wrapper.emitted('logged-out')).toBeTruthy()
  })

  it('reloads all data when the ouid prop changes', async () => {
    mockAll()
    const wrapper = mount(GenericSpaceView, { props: { ouid: 'zhangsan_family' } })
    await flushPromises()
    expect(overviewMock).toHaveBeenCalledTimes(1)

    overviewMock.mockClear()
    resourcesMock.mockClear()
    personsMock.mockClear()
    transactionsMock.mockClear()
    timelineMock.mockClear()

    await wrapper.setProps({ ouid: 'deep_space_fleet' })
    await flushPromises()

    expect(overviewMock).toHaveBeenCalledTimes(1)
    expect(resourcesMock).toHaveBeenCalledTimes(1)
    expect(personsMock).toHaveBeenCalledTimes(1)
    expect(transactionsMock).toHaveBeenCalledTimes(1)
    expect(timelineMock).toHaveBeenCalledTimes(1)
  })
})
