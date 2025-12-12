import React from 'react'

const SourcesViewer = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return null
  }

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-lg">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        Sources ({sources.length})
      </h3>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div
            key={index}
            className="p-2 bg-white rounded border border-gray-200"
          >
            <div className="flex justify-between items-start mb-1">
              <span className="text-xs font-medium text-gray-600">
                {source.document_name}
              </span>
              <span className="text-xs text-gray-500">
                Score: {(source.score * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-xs text-gray-700 line-clamp-2">
              {source.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SourcesViewer

