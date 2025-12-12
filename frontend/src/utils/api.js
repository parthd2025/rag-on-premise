const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const queryRAG = async (question, onChunk, onComplete, onError) => {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'chunk') {
              onChunk(data.content)
            } else if (data.type === 'complete') {
              onComplete(data.content, data.sources || [])
              return
            } else if (data.type === 'error') {
              onError(data.content)
              return
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e)
          }
        }
      }
    }
  } catch (error) {
    onError(error.message)
  }
}

export const uploadDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Upload failed')
  }

  return response.json()
}

export const getDocuments = async (retries = 2) => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      signal: AbortSignal.timeout(10000) // 10 second timeout
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch documents')
    }

    return response.json()
  } catch (error) {
    if (retries > 0 && (error.name === 'AbortError' || error.name === 'TypeError')) {
      // Retry on timeout or network errors
      await new Promise(resolve => setTimeout(resolve, 1000))
      return getDocuments(retries - 1)
    }
    throw error
  }
}

export const deleteDocument = async (documentId) => {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    throw new Error('Failed to delete document')
  }

  return response.json()
}

export const checkHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/health`)
  
  if (!response.ok) {
    throw new Error('Health check failed')
  }

  return response.json()
}

