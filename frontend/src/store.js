import { create } from 'zustand';

export const useStore = create((set) => ({
  messages: [],
  documents: [],
  memory: {},
  models: [],
  useRAG: false,
  useMemory: true,
  tasks: [],
  agentRunning: false,
  agentLog: [],
  suggestions: [],

  addMessage: (role, content) =>
    set((state) => ({
      messages: [...state.messages, { role, content, id: Date.now() }],
    })),

  clearMessages: () => set({ messages: [] }),

  setDocuments: (docs) => set({ documents: docs }),

  setMemory: (mem) => set({ memory: mem }),

  setModels: (mods) => set({ models: mods }),

  toggleRAG: () => set((state) => ({ useRAG: !state.useRAG })),

  toggleMemory: () => set((state) => ({ useMemory: !s.useMemory })),

  setTasks: (tasks) => set({ tasks }),

  setAgentRunning: (running) => set({ agentRunning: running }),

  appendAgentLog: (entry) =>
    set((state) => ({ agentLog: [...state.agentLog, entry] })),

  clearAgentLog: () => set({ agentLog: [] }),

  setSuggestions: (suggestions) => set({ suggestions }),
}));
