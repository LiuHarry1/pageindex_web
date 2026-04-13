import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Send,
  Loader2,
  FileText,
  ChevronDown,
  ChevronRight,
  BookOpen,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { getDocument, chatWithDocument } from '../api/client'
import type { ChatMessage, ChunkItem } from '../types'
import { randomId } from '../utils/id'

function ChunkCard({ chunk, index }: { chunk: ChunkItem; index: number }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 flex items-center gap-2.5 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-indigo-100 text-indigo-700 text-xs font-bold flex-shrink-0">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <span className="text-xs font-medium text-gray-800 truncate block">
            {chunk.title || `Page ${chunk.pages}`}
          </span>
          <span className="text-xs text-gray-400">Page {chunk.pages}</span>
        </div>
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        )}
      </button>
      {expanded && (
        <div className="px-3 py-2.5 border-t border-gray-100 bg-gray-50">
          <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed max-h-72 overflow-y-auto">
            {chunk.content}
          </pre>
        </div>
      )}
    </div>
  )
}

function ReferencesSection({ chunks }: { chunks: ChunkItem[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-3 border-t border-gray-100 pt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors"
      >
        <BookOpen className="w-3.5 h-3.5" />
        {chunks.length} reference{chunks.length !== 1 ? 's' : ''}
        {open ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
      </button>
      {open && (
        <div className="mt-2 space-y-1.5">
          {chunks.map((chunk, i) => (
            <ChunkCard key={i} chunk={chunk} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function ChatPanel() {
  const { docId } = useParams<{ docId: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: doc } = useQuery({
    queryKey: ['document', docId],
    queryFn: () => getDocument(docId!),
    enabled: !!docId,
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const question = input.trim()
    if (!question || loading || !docId) return

    const userMsg: ChatMessage = {
      id: randomId(),
      role: 'user',
      content: question,
    }
    const loadingMsg: ChatMessage = {
      id: randomId(),
      role: 'assistant',
      content: '',
      loading: true,
    }
    setMessages((prev) => [...prev, userMsg, loadingMsg])
    setInput('')
    setLoading(true)

    try {
      const result = await chatWithDocument(docId, question)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? {
                ...m,
                loading: false,
                content: result.answer,
                chunks: result.chunks,
              }
            : m,
        ),
      )
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, loading: false, content: `Error: ${e.message}` }
            : m,
        ),
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-57px)]">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-3 flex items-center gap-4">
        <Link
          to="/"
          className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <FileText className="w-5 h-5 text-indigo-600" />
        <div className="min-w-0">
          <h2 className="font-semibold text-gray-900 truncate text-sm">
            {doc?.doc_name || doc?.filename || 'Loading...'}
          </h2>
          {doc?.doc_description && (
            <p className="text-xs text-gray-500 truncate">{doc.doc_description}</p>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-20 text-gray-400">
            <FileText className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm">Ask a question about this document</p>
            <p className="text-xs mt-1">
              The system will find relevant chunks using agentic retrieval
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl rounded-2xl px-5 py-3 ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              {msg.loading ? (
                <div className="flex items-center gap-2 text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Searching document...</span>
                </div>
              ) : (
                <>
                  <div className={`text-sm prose prose-sm max-w-none ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                  {msg.chunks && msg.chunks.length > 0 && (
                    <ReferencesSection chunks={msg.chunks} />
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            handleSend()
          }}
          className="flex items-center gap-3 max-w-3xl mx-auto"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about this document..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
