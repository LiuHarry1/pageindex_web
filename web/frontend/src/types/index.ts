export interface DocumentInfo {
  id: string
  filename: string
  file_type: string
  status: 'uploading' | 'indexing' | 'ready' | 'failed'
  error_message?: string | null
  page_count?: number | null
  doc_name?: string | null
  doc_description?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface ChunkItem {
  pages: string
  title?: string | null
  content: string
}

export interface RetrieveResponse {
  question: string
  doc_id: string
  doc_name?: string | null
  chunks: ChunkItem[]
  total_tokens: number
}

export interface ChatResponse {
  question: string
  doc_id: string
  doc_name?: string | null
  answer: string
  chunks: ChunkItem[]
  total_tokens: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  chunks?: ChunkItem[]
  loading?: boolean
}
