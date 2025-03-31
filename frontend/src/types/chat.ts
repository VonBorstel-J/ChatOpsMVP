export interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
}

export interface StreamChunk {
    content: string;
    done: boolean;
}

export interface ChatConfig {
    apiUrl: string;
    streamingEnabled: boolean;
    mockMode: boolean;
} 