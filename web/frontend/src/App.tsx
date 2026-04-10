import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { FileText, Upload, MessageSquare } from 'lucide-react'
import DocumentList from './components/DocumentList'
import FileUpload from './components/FileUpload'
import ChatPanel from './components/ChatPanel'

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const { pathname } = useLocation()
  const active = pathname === to || (to !== '/' && pathname.startsWith(to))
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        active
          ? 'bg-indigo-100 text-indigo-700'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      }`}
    >
      {children}
    </Link>
  )
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-600" />
            <span className="text-lg font-bold text-gray-900">PageIndex</span>
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/">
              <FileText className="w-4 h-4" />
              Documents
            </NavLink>
            <NavLink to="/upload">
              <Upload className="w-4 h-4" />
              Upload
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<DocumentList />} />
          <Route path="/upload" element={<FileUpload />} />
          <Route path="/chat/:docId" element={<ChatPanel />} />
        </Routes>
      </main>
    </div>
  )
}
