<script setup lang="ts">
import { ref } from 'vue'
import { sellerChat } from '../api/seller'

interface Message {
  role: 'user' | 'ai'
  content: string
}

const input = ref('')
const messages = ref<Message[]>([])
const loading = ref(false)
const error = ref('')

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return
  error.value = ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  try {
    const result = await sellerChat(text)
    messages.value.push({ role: 'ai', content: result.response })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'AI 处理失败，请稍后重试'
    messages.value.push({ role: 'ai', content: error.value })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="chat">
    <div class="messages" data-test="messages">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="msg"
        :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'"
      >
        {{ msg.content }}
      </div>
    </div>
    <p v-if="error" class="form-error" data-test="chat-error">{{ error }}</p>
    <div class="ask">
      <input
        v-model="input"
        data-test="chat-input"
        type="text"
        placeholder="输入经营查询，如：低库存和采购支出"
        @keyup.enter="send"
      />
      <button
        class="btn primary"
        type="button"
        data-test="chat-send"
        :disabled="loading"
        @click="send"
      >
        {{ loading ? '思考中…' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat {
  display: grid;
  grid-template-rows: 1fr auto auto;
  min-height: 320px;
}
.messages {
  padding: 14px;
  display: grid;
  gap: 10px;
  align-content: start;
  max-height: 340px;
  overflow-y: auto;
}
.msg {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-ai {
  background: #eef7f6;
  border: 1px solid #cae9e6;
  justify-self: start;
  max-width: 92%;
}
.msg-user {
  background: #f2f4f7;
  justify-self: end;
  max-width: 92%;
}
.form-error {
  margin: 0;
  padding: 0 14px 8px;
  font-size: 12px;
  color: var(--red, #b42318);
}
.ask {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--line, #d8dee8);
}
input {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 7px;
  padding: 10px 11px;
  font-size: 13px;
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
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
