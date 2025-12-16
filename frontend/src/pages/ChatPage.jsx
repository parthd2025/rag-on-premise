import React, { useState, useRef, useEffect } from 'react'
import useChatStore from '../store/useChatStore'
import ChatMessage from '../components/ChatMessage'
import SourcesViewer from '../components/SourcesViewer'
import DocumentUploader from '../components/DocumentUploader'
import DocumentList from '../components/DocumentList'
import { queryRAG } from '../utils/api'

const ChatPage = () => {
  const {
    messages,
    isLoading,
    currentSources,
    addMessage,
    updateLastMessage,
    setSources,
    setLoading,
    clearMessages,
  } = useChatStore()

  const [inputValue, setInputValue] = useState('')
  const [uploadRefresh, setUploadRefresh] = useState(0)
  const [showDocuments, setShowDocuments] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (text) => {
    const question = typeof text === 'string' ? text : inputValue.trim()
    if (!question || isLoading) return

    if (typeof text !== 'string') setInputValue('')
    setLoading(true)

    // Add user message
    addMessage({
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    })

    // Add empty assistant message for streaming
    addMessage({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    })

    // Query RAG
    await queryRAG(
      question,
      (chunk) => {
        updateLastMessage(chunk)
      },
      (fullAnswer, sources) => {
        setSources(sources)
        setLoading(false)
      },
      (error) => {
        updateLastMessage(`\n\nError: ${error}`)
        setLoading(false)
        setSources([])
      }
    )
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleUploadSuccess = (result) => {
    setUploadRefresh((prev) => prev + 1)

    let content = `Document "${result.name}" uploaded successfully! (${result.chunks_created} chunks).`
    let suggestions = []

    if (result.valid_questions && result.valid_questions.length > 0) {
      content += "\n\nI've analyzed the document. Here are some suggested questions:"
      suggestions = result.valid_questions
    }

    addMessage({
      role: 'assistant',
      content: content,
      suggestions: suggestions,
      timestamp: new Date().toISOString(),
    })
  }

  const handleUploadError = (error) => {
    alert(`Upload error: ${error}`)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-800">Local RAG</h1>
          <p className="text-sm text-gray-500 mt-1">Free & Local</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4">
            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {showDocuments ? 'Hide' : 'Show'} Documents
            </button>
          </div>

          {showDocuments && (
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">
                Uploaded Documents
              </h2>
              <DocumentUploader
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
              <div className="mt-3">
                <DocumentList onRefresh={uploadRefresh} />
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={clearMessages}
            className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-800">Chat</h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-xl mb-2">Welcome to Local RAG</p>
              <p className="text-sm">
                Upload documents and ask questions to get started
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index}>
              <ChatMessage
                message={message}
                onSuggestionClick={handleSend}
              />
              {message.role === 'assistant' &&
                index === messages.length - 1 &&
                currentSources.length > 0 && (
                  <SourcesViewer sources={currentSources} />
                )}
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg px-4 py-2 shadow-sm">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage

