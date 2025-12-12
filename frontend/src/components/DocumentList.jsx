import React, { useState, useEffect } from 'react'
import { getDocuments, deleteDocument } from '../utils/api'

const DocumentList = ({ onRefresh }) => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const docs = await getDocuments()
      setDocuments(docs)
      setError(null)
    } catch (err) {
      setError('Failed to load documents')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  useEffect(() => {
    if (onRefresh) {
      fetchDocuments()
    }
  }, [onRefresh])

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await deleteDocument(documentId)
      fetchDocuments()
    } catch (err) {
      alert('Failed to delete document')
      console.error(err)
    }
  }

  if (loading) {
    return (
      <div className="p-3 text-center text-gray-500 text-sm">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto mb-2"></div>
        Loading documents...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-3 text-center">
        <div className="text-red-500 text-sm mb-2">{error}</div>
        <button
          onClick={fetchDocuments}
          className="px-3 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100"
        >
          Retry
        </button>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="p-3 text-center text-gray-500 text-sm bg-gray-50 rounded border border-dashed border-gray-300">
        No documents uploaded yet
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="text-xs text-gray-500 mb-2">{documents.length} document(s)</div>
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="font-medium text-gray-800 text-sm truncate" title={doc.name}>
              {doc.name}
            </div>
            <div className="text-xs text-gray-500">
              {doc.chunk_count} chunks • {doc.file_type}
            </div>
          </div>
          <button
            onClick={() => handleDelete(doc.id)}
            className="ml-2 px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-50 rounded flex-shrink-0"
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}

export default DocumentList

