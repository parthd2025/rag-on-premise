import { create } from 'zustand'

// Simple localStorage persistence
const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem('rag-chat-storage')
    return stored ? JSON.parse(stored) : { messages: [] }
  } catch {
    return { messages: [] }
  }
}

const saveToStorage = (state) => {
  try {
    localStorage.setItem('rag-chat-storage', JSON.stringify({ messages: state.messages }))
  } catch {
    // Ignore storage errors
  }
}

const useChatStore = create((set, get) => ({
  messages: loadFromStorage().messages || [],
  isLoading: false,
  currentSources: [],
  
  addMessage: (message) => {
    const newMessages = [...get().messages, message]
    set({ messages: newMessages })
    saveToStorage({ messages: newMessages })
  },
  
  updateLastMessage: (content) => {
    const messages = [...get().messages]
    if (messages.length > 0) {
      messages[messages.length - 1].content += content
      set({ messages })
      saveToStorage({ messages })
    }
  },
  
  setSources: (sources) => set({ currentSources: sources }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  clearMessages: () => {
    set({ messages: [], currentSources: [] })
    saveToStorage({ messages: [] })
  },
}))

export default useChatStore

