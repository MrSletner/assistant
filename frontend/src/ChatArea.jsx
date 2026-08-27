import React, { useState, useEffect, useRef } from 'react';
import { useStore } from './store';
import { chat } from './api';

export const ChatArea = () => {
  const { messages, addMessage, useRAG, useMemory } = useStore();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    addMessage('user', userMessage);
    setLoading(true);

    try {
      const response = await chat(userMessage, useRAG, useMemory);
      
      let fullText = '';
      const reader = response.data.getReader();
      const decoder = new TextDecoder();

      // Add assistant message placeholder
      const messageId = Date.now();
      addMessage('assistant', '');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

        for (const line of lines) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.token) {
              fullText += data.token;
              // Update last message with streamed content
              const state = useStore.getState();
              if (state.messages.length > 0) {
                state.messages[state.messages.length - 1].content = fullText;
              }
            }
          } catch (e) {
            console.error('Parse error:', e);
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      addMessage('assistant', 'Error communicating with the AI. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container flex-1 flex flex-col" ref={containerRef}>
      <div className="messages-area flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${msg.role === 'user' ? 'user' : 'assistant'}`}
          >
            <div className="break-words">
              {msg.content || (msg.role === 'assistant' ? 'Thinking...' : '')}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area border-t border-dark-600 p-4 bg-dark-800">
        <div className="flex gap-2 mb-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" defaultChecked={useMemory} onChange={() => useStore.setState(s => ({ useMemory: !s.useMemory }))} />
            <span className="text-sm text-gray-400">Use Memory</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" onChange={() => useStore.setState(s => ({ useRAG: !s.useRAG }))} />
            <span className="text-sm text-gray-400">Search Documents</span>
          </label>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything..."
            className="input-field flex-1"
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading} className="btn btn-primary">
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};
