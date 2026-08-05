<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    confirmLabel?: string
    cancelLabel?: string
    danger?: boolean
  }>(),
  {
    confirmLabel: '确认',
    cancelLabel: '取消',
    danger: false,
  },
)

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function onConfirm() {
  emit('confirm')
}

function onCancel() {
  emit('cancel')
}
</script>

<template>
  <div v-if="open" class="mask" data-test="confirm-dialog" @click.self="onCancel">
    <div class="box" role="dialog" :aria-label="title">
      <div class="head">
        <div class="title">{{ title }}</div>
      </div>
      <div class="body">
        <p class="text" data-test="confirm-message">{{ message }}</p>
        <div class="actions">
          <button
            type="button"
            class="btn"
            data-test="confirm-cancel"
            @click="onCancel"
          >
            {{ cancelLabel }}
          </button>
          <button
            type="button"
            class="btn"
            :class="danger ? 'danger' : 'primary'"
            data-test="confirm-ok"
            @click="onConfirm"
          >
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(22, 32, 46, 0.45);
  display: grid;
  place-items: center;
  z-index: 120;
}
.box {
  width: 360px;
  max-width: 90vw;
  background: var(--panel, #ffffff);
  border-radius: 10px;
  border: 1px solid var(--line, #d8dee8);
  box-shadow: 0 12px 40px rgba(22, 32, 46, 0.2);
}
.head {
  padding: 14px 18px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.title {
  font-size: 15px;
  font-weight: 750;
}
.body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.text {
  margin: 0;
  font-size: 14px;
  color: var(--ink, #17202a);
  line-height: 1.6;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 7px;
  padding: 9px 14px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn.danger {
  background: var(--red, #b42318);
  color: #ffffff;
  border-color: var(--red, #b42318);
}
</style>
