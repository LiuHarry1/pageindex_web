import type { DocumentInfo, RetrieveResponse, ChatResponse } from '../types'

const BASE = '/api'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const form = new FormData()
  form.append('file', file)
  return request<DocumentInfo>('/documents', { method: 'POST', body: form })
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  return request<DocumentInfo[]>('/documents')
}

export async function getDocument(id: string): Promise<DocumentInfo> {
  return request<DocumentInfo>(`/documents/${id}`)
}

export async function deleteDocument(id: string): Promise<void> {
  return request<void>(`/documents/${id}`, { method: 'DELETE' })
}

export async function getStructure(id: string): Promise<any> {
  return request<any>(`/documents/${id}/structure`)
}

export async function retrieveChunks(
  docId: string,
  question: string,
  model?: string,
): Promise<RetrieveResponse> {
  return request<RetrieveResponse>(`/documents/${docId}/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, model }),
  })
}

export async function chatWithDocument(
  docId: string,
  question: string,
  model?: string,
): Promise<ChatResponse> {
  return request<ChatResponse>(`/documents/${docId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, model }),
  })
}
