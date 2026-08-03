<script setup lang="ts">
withDefaults(
  defineProps<{
    message?: string
  }>(),
  {
    message: '功能即将开放',
  },
)
</script>

<template>
  <section class="placeholder-view" data-test="placeholder-view">
    <div class="card">
      <div class="mark">UA</div>
      <h1 class="title">敬请期待</h1>
      <p class="message" data-test="placeholder-message">{{ message }}</p>
    </div>
  </section>
</template>

<style scoped>
.placeholder-view {
  min-height: 60vh;
  display: grid;
  place-items: center;
}
.card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 10px;
  padding: 40px 48px;
  max-width: 420px;
  width: 100%;
  text-align: center;
  display: grid;
  justify-items: center;
  gap: 10px;
}
.mark {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #243447;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 15px;
}
.title {
  margin: 6px 0 0;
  font-size: 20px;
  font-weight: 800;
}
.message {
  margin: 0;
  color: var(--muted, #637083);
  font-size: 14px;
  line-height: 1.6;
}
</style>
