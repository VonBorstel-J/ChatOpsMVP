import React from 'react';
import { Message } from '../types/chat';
import { format } from 'date-fns';

interface ChatMessageProps {
    message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isAssistant = message.role === 'assistant';
    
    return (
        <div className={`flex w-full ${isAssistant ? 'justify-start' : 'justify-end'} mb-4`}>
            <div className={`max-w-[70%] rounded-lg p-4 ${
                isAssistant ? 'bg-gray-100' : 'bg-blue-500 text-white'
            }`}>
                <div className="flex items-center mb-2">
                    <span className="font-semibold">
                        {isAssistant ? 'Assistant' : 'You'}
                    </span>
                    <span className="text-xs ml-2 opacity-70">
                        {format(message.timestamp, 'HH:mm')}
                    </span>
                </div>
                <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
}; 