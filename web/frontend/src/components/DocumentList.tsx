import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import {
  FileText,
  MessageSquare,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  Upload,
} from 'lucide-react'
import { listDocuments, deleteDocument } from '../api/client'
import type { DocumentInfo } from '../types'

function StatusBadge({ status }: { status: DocumentInfo['status'] }) {
  switch (status) {
    case 'ready':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
          <CheckCircle className="w-3.5 h-3.5" /> Ready
        </span>
      )
    case 'indexing':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Indexing...
        </span>
      )
    case 'uploading':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
          <Clock className="w-3.5 h-3.5" /> Uploading
        </span>
      )
    case 'failed':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
          <AlertCircle className="w-3.5 h-3.5" /> Failed
        </span>
      )
  }
}

export default function DocumentList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: docs, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && data.some((d) => d.status === 'indexing' || d.status === 'uploading')) {
        return 3000
      }
      return false
    },
  })

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this document?')) return
    await deleteDocument(id)
    queryClient.invalidateQueries({ queryKey: ['documents'] })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        <Link
          to="/upload"
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Upload className="w-4 h-4" /> Upload
        </Link>
      </div>

      {!docs || docs.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-200">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">No documents yet</p>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-medium text-sm"
          >
            <Upload className="w-4 h-4" /> Upload your first document
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {docs.map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-gray-200 rounded-xl p-5 flex items-center gap-4 hover:shadow-sm transition-shadow"
            >
              <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 truncate">
                  {doc.doc_name || doc.filename}
                </h3>
                <p className="text-sm text-gray-500 truncate">
                  {doc.filename}
                  {doc.page_count ? ` · ${doc.page_count} pages` : ''}
                </p>
                {doc.error_message && doc.status === 'failed' && (
                  <p className="text-xs text-red-500 mt-1 truncate">{doc.error_message}</p>
                )}
              </div>
              <StatusBadge status={doc.status} />
              <div className="flex items-center gap-2 ml-2">
                <button
                  disabled={doc.status !== 'ready'}
                  onClick={() => navigate(`/chat/${doc.id}`)}
                  className="p-2 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  title="Chat with document"
                >
                  <MessageSquare className="w-5 h-5" />
                </button>
                <button
                  onClick={(e) => handleDelete(doc.id, e)}
                  className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                  title="Delete document"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
