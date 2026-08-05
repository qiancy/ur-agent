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

const props = defineProps<{ ouid: string; activeSection?: string }>()
const emit = defineEmits<{ (e: 'logged-out'): void }>()

const sectionRefs: Record<string, HTMLElement | undefined> = {}

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

watch(
  () => props.activeSection,
  (section) => {
    if (!section) return
    const el = sectionRefs[section]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  },
)

function toggleLocations(name: string) {
  openLocations.value[name] = !openLocations.value[name]
}

function flowLines(key: 'info_flow' | 'logistics_flow' | 'people_flow'): string[] {
  return events.value
    .map((e) => e.payload[key])
    .filter((v): v is string => Boolean(v))
}
</script>

<template>
  <section class="generic-space" data-test="generic-space">
    <div class="topbar">
      <div>
        <h1>空间观察</h1>
        <div class="status">
          {{ props.ouid }} · {{ overview?.space.type ?? '—' }}
        </div>
      </div>
      <button class="btn" type="button" data-test="btn-refresh" @click="load">
        刷新
      </button>
    </div>

    <p v-if="loading" class="hint">加载中…</p>
    <p v-else-if="error" class="form-error" data-test="error">{{ error }}</p>

    <template v-else>
      <section class="block" data-test="block-overview" :ref="(el) => { if (el) sectionRefs['overview'] = el as HTMLElement }">
        <h2>1 空间概览</h2>
        <div class="overview-grid">
          <div class="metric">
            <span class="metric-label">名称</span>
            <span class="metric-value" data-test="ov-name">{{ overview?.space.name ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">类型</span>
            <span class="metric-value" data-test="ov-type">{{ overview?.space.type ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">角色</span>
            <span class="metric-value" data-test="ov-role">{{ overview?.space.role ?? '—' }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">资源数</span>
            <span class="metric-value" data-test="ov-resources">{{ overview?.counts.resources ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">人员数</span>
            <span class="metric-value" data-test="ov-persons">{{ overview?.counts.persons ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">交易数</span>
            <span class="metric-value" data-test="ov-transactions">{{ overview?.counts.transactions ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">最近事件</span>
            <span class="metric-value" data-test="ov-events">{{ overview?.counts.recent_events ?? 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">资金总额</span>
            <span class="metric-value" data-test="ov-funds">{{ overview?.funds ?? 0 }}</span>
          </div>
        </div>
      </section>

      <section class="block" data-test="block-resources" :ref="(el) => { if (el) sectionRefs['resources'] = el as HTMLElement }">
        <h2>2 资源观察</h2>
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
                <span class="chip">{{ r.unit ?? '—' }}</span>
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
      </section>

      <section class="block" data-test="block-persons" :ref="(el) => { if (el) sectionRefs['persons'] = el as HTMLElement }">
        <h2>3 人员观察</h2>
        <ul v-if="persons.length" class="item-list">
          <li v-for="p in persons" :key="p.puid" class="person" data-test="person-row">
            {{ p.name }} · {{ p.puid }} · {{ p.role }}
          </li>
        </ul>
        <p v-else class="hint">暂无成员</p>
      </section>

      <section class="block" data-test="block-timeline" :ref="(el) => { if (el) sectionRefs['timeline'] = el as HTMLElement }">
        <h2>4 时间线</h2>
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
        <p v-else class="hint" data-test="timeline-empty">暂无事件</p>
      </section>

      <section class="block" data-test="block-flows" :ref="(el) => { if (el) sectionRefs['flows'] = el as HTMLElement }">
        <h2>5 多维流向</h2>
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
      </section>
    </template>
  </section>
</template>

<style scoped>
.generic-space {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 750;
}
.status {
  color: var(--muted, #637083);
  font-size: 13px;
  margin-top: 5px;
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
.block {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 16px;
}
.block h2 {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 760;
}
.block h3 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
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
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 4px 9px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
  white-space: nowrap;
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
.person {
  padding: 8px 10px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
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
  border-left: 3px solid var(--teal, #0f766e);
  border: 1px solid var(--line, #d8dee8);
  border-left-width: 3px;
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
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.flow {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 12px;
  min-width: 0;
}
.funds-total {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
}
.hint {
  margin: 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.form-error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
</style>
