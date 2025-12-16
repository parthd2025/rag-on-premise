import React from 'react'

const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-3xl rounded-lg px-4 py-2 ${isUser
          ? 'bg-blue-600 text-white'
          : 'bg-white text-gray-800 shadow-sm'
          }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-3 flex flex-col space-y-2">
            {message.suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => onSuggestionClick && onSuggestionClick(suggestion)}
                className="text-left text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded-md transition-colors border border-blue-200 flex items-center"
              >
                <svg className="w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {message.timestamp && (
          <div
            className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'
              }`}
          >
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage

