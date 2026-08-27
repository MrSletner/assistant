import React, { useState, useRef } from 'react';
import { uploadDocument, listDocuments, deleteDocument, transcribeAudio } from './api';

export const Sidebar = ({ onClose }) => {
  const [tab, setTab] = useState('documents');
  const [documents, setDocuments] = useState([]);
  const fileInputRef = useRef(null);
  const voiceInputRef = useRef(null);

  const handleUploadDocument = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadDocument(file);
      const { data } = await listDocuments();
      setDocuments(data.documents);
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

  const handleDeleteDocument = async (filename) => {
    try {
      await deleteDocument(filename);
      setDocuments(documents.filter(d => d !== filename));
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  const handleTranscribe = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const { data } = await transcribeAudio(file);
      console.log('Transcribed:', data.text);
      // Could add transcribed text to chat
    } catch (error) {
      console.error('Transcription error:', error);
    }
  };

  return (
    <div className="w-64 bg-dark-800 border-r border-dark-600 flex flex-col p-4 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Tools</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-200">✕</button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b border-dark-600">
        {['documents', 'voice', 'memory'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`py-2 px-3 text-sm ${tab === t ? 'border-b-2 border-blue-500' : 'text-gray-400'}`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto space-y-3">
        {tab === 'documents' && (
          <>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-primary w-full"
            >
              + Upload PDF/DOCX
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleUploadDocument}
              hidden
            />
            <div className="space-y-2">
              {documents.map(doc => (
                <div key={doc} className="flex items-center justify-between bg-dark-700 p-2 rounded text-sm">
                  <span className="truncate">{doc}</span>
                  <button
                    onClick={() => handleDeleteDocument(doc)}
                    className="text-red-400 hover:text-red-300"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {tab === 'voice' && (
          <>
            <button
              onClick={() => voiceInputRef.current?.click()}
              className="btn btn-primary w-full"
            >
              🎤 Transcribe Audio
            </button>
            <input
              ref={voiceInputRef}
              type="file"
              accept="audio/*"
              onChange={handleTranscribe}
              hidden
            />
          </>
        )}

        {tab === 'memory' && (
          <div className="space-y-3">
            <button className="btn btn-secondary w-full">📝 Add Profile Note</button>
            <button className="btn btn-secondary w-full">🎯 Add Goal</button>
            <button className="btn btn-secondary w-full">📂 Add Project</button>
            <button className="btn btn-secondary w-full">📔 Add Journal Entry</button>
          </div>
        )}
      </div>
    </div>
  );
};
