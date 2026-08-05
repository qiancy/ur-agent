import { ref } from 'vue'

export const isAuthenticated = ref(false)

export function setAuthenticated(value: boolean): void {
  isAuthenticated.value = value
}
