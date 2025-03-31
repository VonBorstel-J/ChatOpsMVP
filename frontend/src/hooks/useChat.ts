import { useState, useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
import { StreamChunk } from '../types/chat';

export const useChat = () => {
    const { addMessage, setLoading, setError } = useChatStore();
    const [isStreaming, setIsStreaming] = useState(false);

    const sendMessage = useCallback(async (content: string) => {
        console.log('[Chat] Sending message:', { content });
        try {
            setLoading(true);
            setError(null);
            
            // Add user message
            addMessage(content, 'user');
            console.log('[Chat] Added user message to store');

            // Send to backend
            console.log('[Chat] Sending request to backend...');
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: [{
                        role: 'user',
                        content: content
                    }],
                    stream: true
                }),
            });

            console.log('[Chat] Backend response status:', response.status);
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[Chat] Backend error:', { status: response.status, error: errorText });
                throw new Error(`Failed to send message: ${response.status} ${errorText}`);
            }

            // Handle streaming response
            const reader = response.body?.getReader();
            if (!reader) {
                console.error('[Chat] No response stream available');
                throw new Error('No response stream available');
            }

            setIsStreaming(true);
            console.log('[Chat] Starting to stream response');
            let accumulatedContent = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) {
                    console.log('[Chat] Stream complete');
                    break;
                }

                // Parse the chunk
                const chunk = new TextDecoder().decode(value);
                console.log('[Chat] Received chunk:', chunk);
                const data: StreamChunk = JSON.parse(chunk);
                
                accumulatedContent += data.content;
                
                if (data.done) {
                    console.log('[Chat] Message complete, adding to store');
                    addMessage(accumulatedContent, 'assistant');
                    break;
                }
            }
        } catch (err) {
            console.error('[Chat] Error in sendMessage:', err);
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
            setIsStreaming(false);
            console.log('[Chat] Request complete');
        }
    }, [addMessage, setLoading, setError]);

    return {
        sendMessage,
        isStreaming
    };
}; 