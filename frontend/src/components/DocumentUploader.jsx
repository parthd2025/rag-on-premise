import React, { useState } from 'react'
import { uploadDocument } from '../utils/api'

const DocumentUploader = ({ onUploadSuccess, onUploadError }) => {
  const [isUploading, setIsUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleFile = async (file) => {
    if (!file) return

    const allowedTypes = [
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    if (!allowedTypes.includes(file.type)) {
      onUploadError('Please upload a PDF, TXT, or DOCX file')
      return
    }

    setIsUploading(true)

    try {
      const result = await uploadDocument(file)
      onUploadSuccess(result)
    } catch (error) {
      onUploadError(error.message || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  return (
    <div className="mb-3">
      <div
        className={`border-2 border-dashed rounded-lg p-3 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-white'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          accept=".pdf,.txt,.docx"
          onChange={handleChange}
          disabled={isUploading}
        />
        <label
          htmlFor="file-upload"
          className="cursor-pointer flex flex-col items-center"
        >
          {isUploading ? (
            <>
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mb-1"></div>
              <span className="text-gray-600 text-sm">Uploading...</span>
            </>
          ) : (
            <>
              <svg
                className="w-8 h-8 text-gray-400 mb-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p className="text-gray-600 text-sm">
                Drag and drop a document here, or click to select
              </p>
              <p className="text-xs text-gray-500">
                Supports PDF, TXT, and DOCX files
              </p>
            </>
          )}
        </label>
      </div>
    </div>
  )
}

export default DocumentUploader

