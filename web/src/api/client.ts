export const TOKEN_KEY = 'unires_token'

export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(apiUrl(path), { ...options, headers })

  if (response.status === 401) {
    clearToken()
  }

  if (!response.ok) {
    throw new ApiError(response.status, await response.text())
  }

  return (await response.json()) as T
}
