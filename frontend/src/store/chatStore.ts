import { create } from 'zustand';
import { ChatState, Message } from '../types/chat';
import { v4 as uuidv4 } from 'uuid';

interface ChatStore extends ChatState {
    addMessage: (content: string, role: 'user' | 'assistant') => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
    messages: [],
    isLoading: false,
    error: null,
    
    addMessage: (content, role) => set((state) => ({
        messages: [...state.messages, {
            id: uuidv4(),
            content,
            role,
            timestamp: new Date()
        }]
    })),
    
    setLoading: (loading) => set({ isLoading: loading }),
    
    setError: (error) => set({ error }),
    
    clearMessages: () => set({ messages: [] })
})); 