import React, { useState, useEffect } from 'react';
import { ChatArea } from './ChatArea';
import { Sidebar } from './Sidebar';
import { useStore } from './store';
import { listDocuments, listModels } from './api';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [model, setModel] = useState('llama2');
  const { setModels } = useStore();

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const { data } = await listModels();
      const models = data.models || [];
      setModels(models);
      if (models.length > 0) {
        setModel(models[0].name);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  return (
    <div className="flex h-screen bg-dark-900 text-gray-100">
      {/* Sidebar */}
      {sidebarOpen && <Sidebar onClose={() => setSidebarOpen(false)} />}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-dark-800 border-b border-dark-600 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-gray-200"
            >
              ☰
            </button>
            <h1 className="text-xl font-bold">Local AI Assistant</h1>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="bg-dark-700 border border-dark-600 rounded px-3 py-2 text-sm"
            >
              <option value="llama2">Llama 2</option>
              <option value="mistral">Mistral</option>
              <option value="neural-chat">Neural Chat</option>
            </select>
            <a href="#" className="text-gray-400 hover:text-gray-200">⚙️</a>
          </div>
        </div>

        {/* Chat Area */}
        <ChatArea />
      </div>
    </div>
  );
}

export default App;
