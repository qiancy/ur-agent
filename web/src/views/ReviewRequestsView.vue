<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  approveJoinRequest,
  getSpaceJoinRequests,
  rejectJoinRequest,
  type SpaceJoinRequest,
} from '../api/spaceGovernance'
import JoinRequestTable from '../components/JoinRequestTable.vue'

const props = defineProps<{
  ouid: string
  orgType: string
  role: string
  puid: string
  personName: string
  organizationName: string
}>()

const isOwnerOrAdmin = computed(
  () => props.role === 'owner' || props.role === 'admin',
)

const requests = ref<SpaceJoinRequest[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await getSpaceJoinRequests('pending')
    requests.value = data.requests
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载申请失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isOwnerOrAdmin.value) load()
})

async function onApprove(req: SpaceJoinRequest) {
  error.value = ''
  try {
    await approveJoinRequest(req.request_uid)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '通过失败'
  }
}

async function onReject(req: SpaceJoinRequest) {
  error.value = ''
  try {
    await rejectJoinRequest(req.request_uid)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '拒绝失败'
  }
}
</script>

<template>
  <section class="review-requests-view" data-test="review-requests-view">
    <h2 class="title">审核申请</h2>
    <p class="sub">{{ organizationName }} · {{ ouid }}</p>
    <div v-if="!isOwnerOrAdmin" class="no-perm" data-test="review-no-perm">
      你没有审核权限。只有该空间的 owner 或 admin 可以审核加入申请。
    </div>
    <template v-else>
      <p v-if="error" class="error" data-test="review-error">{{ error }}</p>
      <JoinRequestTable
        :requests="requests"
        :can-approve="true"
        @approve="onApprove"
        @reject="onReject"
      />
    </template>
  </section>
</template>

<style scoped>
.review-requests-view {
  max-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}
.sub {
  margin: 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
.no-perm {
  padding: 18px;
  background: #fdf3f3;
  border: 1px solid #f3c6c6;
  border-radius: 8px;
  color: #a33;
  font-size: 14px;
}
.error {
  margin: 0;
  font-size: 13px;
  color: var(--red, #b42318);
}
</style>
