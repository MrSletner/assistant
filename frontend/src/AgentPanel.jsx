import React, { useState, useEffect } from 'react';
import { useStore } from './store';
import {
  listTasks, createTask, updateTask, deleteTask,
  runAgent, suggestNextSteps,
} from './api';

const STATUS_STYLE = {
  todo: 'text-yellow-400',
  in_progress: 'text-blue-400',
  done: 'text-green-400 line-through opacity-60',
};

export const AgentPanel = () => {
  const {
    tasks, setTasks,
    agentRunning, setAgentRunning,
    agentLog, appendAgentLog, clearAgentLog,
    suggestions, setSuggestions,
  } = useStore();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [goal, setGoal] = useState('');

  const refresh = async () => {
    try {
      const { data } = await listTasks();
      setTasks(data.tasks);
    } catch (e) {
      console.error('Failed to load tasks', e);
    }
  };

  useEffect(() => { refresh(); }, []);

  const handleAddTask = async () => {
    if (!title.trim()) return;
    try {
      await createTask(title, description);
      setTitle('');
      setDescription('');
      refresh();
    } catch (e) {
      console.error('Failed to add task', e);
    }
  };

  const handleComplete = async (id) => {
    await updateTask(id, { status: 'done' });
    refresh();
  };

  const handleDelete = async (id) => {
    await deleteTask(id);
    refresh();
  };

  const handleAddSuggestion = async (s) => {
    await createTask(s.title, s.description || s.reason || '');
    setSuggestions(suggestions.filter((x) => x !== s));
    refresh();
  };

  const handleSuggest = async () => {
    try {
      const { data } = await suggestNextSteps();
      setSuggestions(data.suggestions || []);
    } catch (e) {
      console.error('Failed to suggest', e);
    }
  };

  const handleRun = async (taskId = null, runGoal = null) => {
    if (agentRunning) return;
    setAgentRunning(true);
    clearAgentLog();
    appendAgentLog({ type: 'info', text: 'Starting agent…' });
    try {
      const response = await runAgent(taskId, runGoal);
      const reader = response.data.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const evt = JSON.parse(line.slice(6));
            if (evt.event === 'plan') {
              appendAgentLog({ type: 'plan', steps: evt.steps });
            } else if (evt.event === 'step') {
              appendAgentLog({
                type: 'step',
                index: evt.index,
                thought: evt.thought,
                tool: evt.tool,
                args: evt.args,
              });
            } else if (evt.event === 'observation') {
              appendAgentLog({
                type: 'observation',
                index: evt.index,
                tool: evt.tool,
                result: evt.result,
              });
            } else if (evt.event === 'done') {
              appendAgentLog({ type: 'done', summary: evt.summary });
            } else if (evt.event === 'error') {
              appendAgentLog({ type: 'error', text: evt.error });
            }
          } catch (e) { /* skip partial */ }
        }
      }
      refresh();
    } catch (e) {
      appendAgentLog({ type: 'error', text: String(e) });
    } finally {
      setAgentRunning(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Add task */}
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="New task title…"
        className="input-field text-sm"
      />
      <input
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Details (optional)"
        className="input-field text-sm"
      />
      <button onClick={handleAddTask} className="btn btn-primary w-full text-sm">
        + Schedule Task
      </button>

      {/* Run on a goal */}
      <div className="flex gap-2">
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Or run agent on a goal…"
          className="input-field text-sm flex-1"
          disabled={agentRunning}
        />
        <button
          onClick={() => handleRun(null, goal || undefined)}
          disabled={agentRunning || !goal.trim()}
          className="btn btn-secondary text-sm whitespace-nowrap"
        >
          {agentRunning ? 'Running…' : '▶ Run'}
        </button>
      </div>

      <button
        onClick={handleSuggest}
        disabled={agentRunning}
        className="btn btn-secondary w-full text-sm"
      >
        ✨ Suggest Next Step
      </button>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          {suggestions.map((s, i) => (
            <div key={i} className="bg-dark-700 p-2 rounded text-sm">
              <div className="font-medium">{s.title}</div>
              {s.reason && <div className="text-xs text-gray-400 mt-1">{s.reason}</div>}
              <div className="flex gap-2 mt-1">
                <button
                  onClick={() => handleAddSuggestion(s)}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  + Add as task
                </button>
                <button
                  onClick={() => setSuggestions(suggestions.filter((_, j) => j !== i))}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Agent log */}
      {agentLog.length > 0 && (
        <div className="bg-dark-900 border border-dark-600 rounded p-2 max-h-48 overflow-y-auto space-y-1 text-xs">
          {agentLog.map((log, i) => {
            if (log.type === 'info') return <div key={i} className="text-gray-400">{log.text}</div>;
            if (log.type === 'plan')
              return (
                <div key={i} className="text-purple-300">
                  <span className="font-medium">Plan:</span>
                  <ol className="list-decimal ml-4">
                    {log.steps.map((s, j) => <li key={j}>{s}</li>)}
                  </ol>
                </div>
              );
            if (log.type === 'step')
              return (
                <div key={i} className="text-blue-300">
                  <span className="font-medium">Step {log.index + 1}:</span> {log.thought}
                  {log.tool && <div className="text-gray-400 ml-2">→ {log.tool}</div>}
                </div>
              );
            if (log.type === 'observation')
              return (
                <div key={i} className="text-gray-400 ml-4">
                  ↳ {String(log.result).slice(0, 160)}
                </div>
              );
            if (log.type === 'done')
              return <div key={i} className="text-green-400 font-medium">✓ {log.summary}</div>;
            if (log.type === 'error')
              return <div key={i} className="text-red-400">✗ {log.text}</div>;
            return null;
          })}
        </div>
      )}

      {/* Agenda */}
      <div className="space-y-2 pt-2 border-t border-dark-600">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Agenda</div>
        {tasks.length === 0 && <div className="text-xs text-gray-500">No tasks yet.</div>}
        {tasks.map((task) => (
          <div key={task.id} className="bg-dark-700 p-2 rounded text-sm">
            <div className={`font-medium ${STATUS_STYLE[task.status] || ''}`}>
              {task.title}
            </div>
            {task.description && <div className="text-xs text-gray-400 mt-1">{task.description}</div>}
            <div className="flex gap-2 mt-1">
              {task.status !== 'done' && (
                <>
                  <button
                    onClick={() => handleRun(task.id)}
                    disabled={agentRunning}
                    className="text-xs text-blue-400 hover:text-blue-300"
                  >
                    ▶ Run
                  </button>
                  <button
                    onClick={() => handleComplete(task.id)}
                    className="text-xs text-green-400 hover:text-green-300"
                  >
                    ✓ done
                  </button>
                </>
              )}
              <button
                onClick={() => handleDelete(task.id)}
                className="text-xs text-red-400 hover:text-red-300"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
