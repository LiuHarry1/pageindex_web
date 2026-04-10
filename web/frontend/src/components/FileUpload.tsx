import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import {  FileUp, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { uploadDocument } from '../api/client'

export default function FileUpload() {
  const navigate = useNavigate()
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      const file = acceptedFiles[0]
      setUploading(true)
      setError(null)
      setSuccess(false)
      try {
        await uploadDocument(file)
        setSuccess(true)
        setTimeout(() => navigate('/'), 1500)
      } catch (e: any) {
        setError(e.message || 'Upload failed')
      } finally {
        setUploading(false)
      }
    },
    [navigate],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/markdown': ['.md', '.markdown'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload Document</h1>
      <p className="text-gray-500 mb-8">
        Upload a PDF or Markdown file to build a hierarchical index for intelligent retrieval.
      </p>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-indigo-400 bg-indigo-50'
            : uploading
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          {uploading ? (
            <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
          ) : success ? (
            <CheckCircle className="w-12 h-12 text-green-500" />
          ) : (
            <FileUp className="w-12 h-12 text-gray-400" />
          )}

          {uploading ? (
            <p className="text-gray-600 font-medium">Uploading...</p>
          ) : success ? (
            <p className="text-green-600 font-medium">Upload successful! Redirecting...</p>
          ) : isDragActive ? (
            <p className="text-indigo-600 font-medium">Drop the file here</p>
          ) : (
            <>
              <p className="text-gray-600 font-medium">
                Drag & drop a file here, or click to browse
              </p>
              <p className="text-sm text-gray-400">Supports PDF, Markdown (.md)</p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 text-red-600 bg-red-50 px-4 py-3 rounded-lg">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  )
}
