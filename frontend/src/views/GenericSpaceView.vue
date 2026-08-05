<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ApiError } from '../api/client'
import {
  getSpaceDashboard,
  type SpaceOverviewData,
  type SpacePerson,
  type SpaceResourcesData,
  type SpaceTransaction,
  type TimelineEvent,
} from '../api/spaces'
import PageHeader from '../components/PageHeader.vue'
import SectionCard from '../components/SectionCard.vue'
import StatusChip from '../components/StatusChip.vue'
import EmptyState from '../components/EmptyState.vue'

const props = defineProps<{ ouid: string }>()
const emit = defineEmits<{ (e: 'logged-out'): void }>()

const overview = ref<SpaceOverviewData | null>(null)
const grouped = ref<SpaceResourcesData | null>(null)
const persons = ref<SpacePerson[]>([])
const transactions = ref<SpaceTransaction[]>([])
const events = ref<TimelineEvent[]>([])
const loading = ref(true)
const error = ref('')

const openLocations = ref<Record<string, boolean>>({})

const resourceGroups = computed(() => {
  const g = grouped.value?.grouped
  return [
    { key: 'physical', label: '实物资源', items: g?.physical ?? [] },
    { key: 'knowledge', label: '知识资源', items: g?.knowledge ?? [] },
    { key: 'financial', label: '资金资源', items: g?.financial ?? [] },
    { key: 'human', label: '人力资源', items: g?.human ?? [] },
  ]
})

function handleError(e: unknown): boolean {
  if (e instanceof ApiError && e.status === 401) {
    emit('logged-out')
    return true
  }
  return false
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const dashboard = await getSpaceDashboard()
    overview.value = dashboard.overview
    grouped.value = dashboard.resources
    persons.value = dashboard.persons
    transactions.value = dashboard.transactions
    events.value = dashboard.timeline.events
  } catch (e) {
    if (!handleError(e)) {
      error.value = e instanceof Error ? e.message : '空间数据加载失败'
    }
  } finally {
    loading.value = false
  }
}

watch(() => props.ouid, load, { immediate: true })

function toggleLocations(name: string) {
  openLocations.value[name] = !openLocations.value[name]
}

function flowLines(key: 'info_flow' | 'logistics_flow' | 'people_flow'): string[] {
  return events.value
    .map((e) => e.payload[key])
    .filter((v): v is string => Boolean(v))
}

const radarCards = computed(() => {
  if (!overview.value) return []
  const totalResources = overview.value.counts.resources
  const totalPersons = overview.value.counts.persons
  const totalTransactions = overview.value.counts.transactions
  const recentEvents = overview.value.counts.recent_events
  const funds = overview.value.funds
  const lastResource = grouped.value?.grouped.physical[0] ?? grouped.value?.grouped.knowledge[0] ?? null
  const lastPerson = persons.value[0] ?? null
  const lastTx = transactions.value[0] ?? null
  const lastEvent = events.value[0] ?? null

  return [
    {
      key: 'resources',
      label: 'Resources',
      value: totalResources,
      unit: '资源',
      hint: lastResource ? `最近：${lastResource.name}` : '暂无资源',
    },
    {
      key: 'persons',
      label: 'Persons',
      value: totalPersons,
      unit: '人员',
      hint: lastPerson ? `最近：${lastPerson.name}` : '暂无人员',
    },
    {
      key: 'finance',
      label: 'Finance',
      value: funds,
      unit: lastTx ? `${totalTransactions} 笔交易` : '无交易',
      hint: lastTx ? `最近：${lastTx.from_party_name} → ${lastTx.to_party_name}` : '暂无交易',
    },
    {
      key: 'knowledge',
      label: 'Knowledge',
      value: recentEvents,
      unit: '事件',
      hint: lastEvent ? `最近：${lastEvent.title}` : '暂无事件',
    },
  ]
})
</script>

<template>
  <section class="generic-space" data-test="generic-space">
    <PageHeader
      :title="overview?.space.name ?? '空间观察'"
      :status="overview ? `${overview.space.type} · ${overview.space.role}` : ''"
    >
      <button class="btn" type="button" data-test="btn-refresh" @click="load">
        刷新
      </button>
    </PageHeader>

    <p v-if="loading" class="hint">加载中…</p>
    <p v-else-if="error" class="form-error" data-test="error">{{ error }}</p>

    <template v-else-if="overview">
      <SectionCard title="1 空间概览" data-test="block-overview">
        <div class="overview-grid">
          <div class="metric">
            <span class="metric-label">名称</span>
            <span class="metric-value" data-test="ov-name">{{ overview.space.name ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">类型</span>
            <span class="metric-value" data-test="ov-type">{{ overview.space.type ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">角色</span>
            <span class="metric-value" data-test="ov-role">{{ overview.space.role ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">资源数</span>
            <span class="metric-value" data-test="ov-resources">{{ overview.counts.resources ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">人员数</span>
            <span class="metric-value" data-test="ov-persons">{{ overview.counts.persons ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">交易数</span>
            <span class="metric-value" data-test="ov-transactions">{{ overview.counts.transactions ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">最近事件</span>
            <span class="metric-value" data-test="ov-events">{{ overview.counts.recent_events ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">资金总额</span>
            <span class="metric-value" data-test="ov-funds">{{ overview.funds ?? 0 }}</span>
          </div>
        </div>
      </SectionCard>

      <div class="radar-row">
        <div v-for="card in radarCards" :key="card.key" class="radar-card" :data-test="`radar-${card.key}`">
          <div class="radar-label">{{ card.label }}</div>
          <div class="radar-value">{{ card.value }} <span class="radar-unit">{{ card.unit }}</span></div>
          <div class="radar-hint">{{ card.hint }}</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="left-col">
          <SectionCard title="2 资源观察" data-test="block-resources">
            <div
              v-for="group in resourceGroups"
              :key="group.key"
              class="group"
              :data-test="`group-${group.key}`"
            >
              <h3>{{ group.label }}（{{ group.items.length }}）</h3>
              <ul v-if="group.items.length" class="item-list">
                <li v-for="r in group.items" :key="r.name" class="resource" :data-test="`resource-${r.name}`">
                  <div class="resource-head">
                    <span class="resource-name">{{ r.name }}</span>
                    <StatusChip :label="r.unit ?? '—'" />
                  </div>
                  <p class="resource-desc" data-test="resource-amount">
                    数量/金额：{{ r.amount ?? '—' }}
                  </p>
                  <p class="resource-desc">{{ r.description ?? '—' }}</p>
                  <template
                    v-if="group.key === 'physical' && r.locations && r.locations.length"
                  >
                    <button
                      class="btn small"
                      type="button"
                      :data-test="`toggle-locations-${r.name}`"
                      @click="toggleLocations(r.name)"
                    >
                      {{ openLocations[r.name] ? '收起库位' : '展开库位' }}
                    </button>
                    <table v-if="openLocations[r.name]" class="loc-table" data-test="locations-table">
                      <thead>
                        <tr>
                          <th>仓库</th>
                          <th>库位</th>
                          <th class="num">数量</th>
                          <th>单位</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(loc, i) in r.locations" :key="i" data-test="location-row">
                          <td>{{ loc.warehouse_code }}</td>
                          <td>{{ loc.location_path }}</td>
                          <td class="num">{{ loc.quantity }}</td>
                          <td>{{ loc.unit }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </template>
                </li>
              </ul>
              <p v-else class="hint">暂无{{ group.label }}</p>
            </div>
          </SectionCard>

          <SectionCard title="3 人员观察" data-test="block-persons" style="margin-top: 16px;">
            <ul v-if="persons.length" class="item-list persons-list">
              <li v-for="p in persons" :key="p.puid" class="person" data-test="person-row">
                <span class="avatar">{{ p.name.charAt(0) }}</span>
                <div class="person-info">
                  <span class="person-name">{{ p.name }}</span>
                  <span class="person-role">{{ p.role }}</span>
                </div>
                <StatusChip :label="p.puid" variant="default" />
              </li>
            </ul>
            <EmptyState
              v-else
              type="readonly"
              title="暂无成员"
              description="该空间还没有人员，请先添加成员。"
            />
          </SectionCard>
        </div>

        <div class="right-col">
          <SectionCard title="4 时间线" data-test="block-timeline">
            <ol v-if="events.length" class="timeline">
              <li
                v-for="e in events"
                :key="`${e.campaign_code}-${e.seq}`"
                class="event"
                data-test="event-row"
              >
                <div class="event-head">
                  <span class="seq">#{{ e.seq }}</span>
                  <span class="event-title">{{ e.title }}</span>
                  <span class="chip">{{ e.campaign_name }}（{{ e.campaign_code }}）</span>
                </div>
                <p class="event-desc">{{ e.description ?? '—' }}</p>
                <div
                  v-if="e.payload.info_flow || e.payload.logistics_flow || e.payload.people_flow || e.payload.risk"
                  class="dims"
                >
                  <span v-if="e.payload.info_flow" class="dim" data-test="dim-info">信息流：{{ e.payload.info_flow }}</span>
                  <span v-if="e.payload.logistics_flow" class="dim" data-test="dim-logistics">物流：{{ e.payload.logistics_flow }}</span>
                  <span v-if="e.payload.people_flow" class="dim" data-test="dim-people">人流：{{ e.payload.people_flow }}</span>
                  <span v-if="e.payload.risk" class="dim" data-test="dim-risk">风险：{{ e.payload.risk }}</span>
                </div>
              </li>
            </ol>
            <EmptyState
              v-else
              type="readonly"
              title="暂无事件"
              description="空间内暂无时间线事件。"
              data-test="timeline-empty"
            />
          </SectionCard>

          <SectionCard title="5 多维流向" data-test="block-flows" style="margin-top: 16px;">
            <div class="flows-grid">
              <div class="flow" data-test="flow-info">
                <h3>信息流</h3>
                <ul class="item-list">
                  <li v-for="(k, i) in (grouped?.grouped.knowledge ?? [])" :key="`k${i}`">
                    {{ k.name }}：{{ k.description ?? '—' }}
                  </li>
                  <li v-for="(f, i) in flowLines('info_flow')" :key="`if${i}`">
                    {{ f }}
                  </li>
                </ul>
                <p
                  v-if="(grouped?.grouped.knowledge ?? []).length === 0 && flowLines('info_flow').length === 0"
                  class="hint"
                >
                  暂无信息流
                </p>
              </div>

              <div class="flow" data-test="flow-logistics">
                <h3>物流</h3>
                <ul class="item-list">
                  <li v-for="(p, i) in (grouped?.grouped.physical ?? [])" :key="`p${i}`">
                    {{ p.name }}：{{ p.amount ?? '—' }}{{ p.unit ?? '' }}
                  </li>
                  <li v-for="(f, i) in flowLines('logistics_flow')" :key="`lf${i}`">
                    {{ f }}
                  </li>
                </ul>
                <p
                  v-if="(grouped?.grouped.physical ?? []).length === 0 && flowLines('logistics_flow').length === 0"
                  class="hint"
                >
                  暂无物流
                </p>
              </div>

              <div class="flow" data-test="flow-people">
                <h3>人流</h3>
                <ul class="item-list">
                  <li v-for="p in persons" :key="p.puid">
                    {{ p.name }}（{{ p.role }}）
                  </li>
                  <li v-for="(f, i) in flowLines('people_flow')" :key="`pe${i}`">
                    {{ f }}
                  </li>
                </ul>
                <p
                  v-if="persons.length === 0 && flowLines('people_flow').length === 0"
                  class="hint"
                >
                  暂无人流
                </p>
              </div>

              <div class="flow" data-test="flow-funds">
                <h3>资金流</h3>
                <p class="funds-total" data-test="funds-total">
                  资金总额：{{ overview?.funds ?? 0 }}
                </p>
                <table v-if="transactions.length" class="tx-table">
                  <thead>
                    <tr>
                      <th>参与方</th>
                      <th class="num">金额</th>
                      <th>分类</th>
                      <th>说明</th>
                      <th>时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in transactions" :key="t.transaction_uid" data-test="tx-row">
                      <td>{{ t.from_party_name }} → {{ t.to_party_name }}</td>
                      <td class="num">{{ t.amount }}</td>
                      <td>{{ t.category }}</td>
                      <td>{{ t.description ?? '—' }}</td>
                      <td>{{ t.created_at }}</td>
                    </tr>
                  </tbody>
                </table>
                <p v-else class="hint">暂无资金流水</p>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.generic-space {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.hint {
  margin: 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.form-error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #ef4444);
}
.radar-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(200px, 1fr));
  gap: 12px;
}
.radar-card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.radar-label {
  font-size: 12px;
  color: var(--muted, #637083);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.radar-value {
  font-size: 22px;
  font-weight: 750;
  color: var(--ink, #17202a);
  line-height: 1.2;
}
.radar-unit {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted, #637083);
  margin-left: 4px;
}
.radar-hint {
  font-size: 12px;
  color: var(--muted, #637083);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}
.metric {
  padding: 12px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric-label {
  font-size: 12px;
  color: var(--muted, #637083);
}
.metric-value {
  font-size: 18px;
  font-weight: 650;
  color: var(--ink, #17202a);
  text-align: right;
}
.grid-2 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.group {
  margin-bottom: 14px;
}
.group:last-child {
  margin-bottom: 0;
}
.item-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
}
.resource {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 10px 12px;
}
.resource-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.resource-name {
  font-weight: 700;
}
.resource-desc {
  margin: 6px 0 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.persons-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.person {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4338ca;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.person-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}
.person-name {
  font-weight: 700;
  font-size: 13px;
  color: var(--ink, #17202a);
}
.person-role {
  font-size: 12px;
  color: var(--muted, #637083);
}
.timeline {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.event {
  border: 1px solid var(--line, #d8dee8);
  border-left: 3px solid var(--teal, #0f766e);
  border-radius: 8px;
  padding: 10px 12px;
}
.event-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.seq {
  font-weight: 800;
  color: var(--teal, #0f766e);
  font-size: 13px;
}
.event-title {
  font-weight: 700;
}
.event-desc {
  margin: 6px 0 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.dims {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.dim {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 12px;
  background: #fbfcfe;
}
.flows-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.flow {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 12px;
  min-width: 0;
}
.flow h3 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
}
.funds-total {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
}
.loc-table,
.tx-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-top: 8px;
}
.loc-table th,
.tx-table th,
.loc-table td,
.tx-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #edf0f4;
  text-align: left;
}
.loc-table th,
.tx-table th {
  color: var(--muted, #637083);
  font-size: 12px;
  font-weight: 700;
  background: #fafbfc;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 4px 9px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
  white-space: nowrap;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 10px 13px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.small {
  padding: 6px 10px;
  font-size: 12px;
}
.btn:hover {
  background: #f4f6f8;
}

@media (max-width: 1280px) {
  .radar-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 768px) {
  .radar-row {
    grid-template-columns: 1fr;
  }
}
</style>
