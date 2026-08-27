"""
Autonomous task agent.

A plan -> act -> verify loop driven by Ollama's /api/chat. The agent is given a
goal (a scheduled task or an explicit instruction), plans a short list of
steps, then repeatedly chooses an action from a small toolset, executes it,
and feeds the observation back until it reports done.

It can also propose the "next logical step" by analysing the current agenda,
memory and recent conversation patterns.
"""
import json
import re
import os
from typing import AsyncIterator

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama2")
MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "6"))

TOOLS = [
    {
        "name": "recall_memory",
        "description": "Read a memory file to remember what you have learned about the user.",
        "args": {"type": "one of: profile, goals, projects, journal"},
    },
    {
        "name": "save_memory",
        "description": "Persist a learning, preference or insight so future runs remember it.",
        "args": {"type": "profile|goals|projects|journal", "title": "short title", "content": "what to remember"},
    },
    {
        "name": "list_tasks",
        "description": "See the current agenda of scheduled/todo tasks.",
        "args": {},
    },
    {
        "name": "add_task",
        "description": "Schedule a follow-up task that a future agent run should pick up.",
        "args": {"title": "short title", "description": "what needs doing"},
    },
    {
        "name": "complete_task",
        "description": "Mark a task on the agenda finished, with a short result note.",
        "args": {"id": "task id", "result": "short note on what was done"},
    },
    {
        "name": "finish",
        "description": "Stop acting and report the final outcome.",
        "args": {"summary": "concise summary of what was accomplished"},
    },
]


def _tool_descriptions() -> str:
    return "\n".join(
        f"- {t['name']}: {t['description']} args={json.dumps(t['args'])}" for t in TOOLS
    )


SYSTEM_PROMPT = (
    "You are a thoughtful autonomous assistant executing a task for the user.\n"
    "Break the task into a few concrete steps, then use the available tools to make "
    "progress. When the task is complete, call finish.\n"
    "You MUST reply with ONLY a single JSON object, nothing else.\n"
    "Examples of correct responses:\n"
    '{"thought":"I need to remember what the user likes first.","action":{"tool":"recall_memory","args":{"type":"profile"}}}\n'
    '{"thought":"Drafting the note and saving it for next time.","action":{"tool":"save_memory","args":{"type":"journal","title":"welcome note drafted","content":"Welcome to the community!"}}}\n'
    '{"thought":"Goal complete.","action":{"tool":"finish","args":{"summary":"Drafted and saved the welcome note"}}}\n'
    "Tools:\n"
    f"{_tool_descriptions()}\n"
    "Rules: call exactly one tool per step. Use finish when done. "
    "Never write the example values back; always use real tool names and real args."
)


def _extract_json(text: str) -> dict | None:
    """Leniently pull the first JSON object out of a model response."""
    # Prefer a fenced ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        candidate = m.group(1)
    else:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        candidate = m.group(0)
    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict) and "action" in obj:
            return obj
    except json.JSONDecodeError:
        # Try repairing common trailing-comma issues
        try:
            obj = json.loads(re.sub(r",\s*}", "}", re.sub(r",\s*]", "]", candidate)))
            if isinstance(obj, dict) and "action" in obj:
                return obj
        except json.JSONDecodeError:
            return None
    return None


async def _chat(messages: list) -> str:
    """One non-streaming chat turn against Ollama, returning the full text."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.4},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")


def _execute_tool(action: dict, context: dict) -> str:
    """Run a tool locally and return a short observation string."""
    from main import save_memory, load_memory  # lazy import to avoid a cycle
    import tasks as taskstore

    tool = action.get("tool")
    args = action.get("args", {}) or {}

    if tool == "recall_memory":
        return load_memory(args.get("type", "profile")) or "(no memory of that type yet)"
    if tool == "save_memory":
        save_memory(args.get("title", "agent note"), args.get("content", ""), args.get("type", "journal"))
        return "saved to memory"
    if tool == "list_tasks":
        ts = taskstore.list_tasks()
        if not ts:
            return "agenda is empty"
        return json.dumps(
            [{"id": t["id"], "title": t["title"], "status": t["status"]} for t in ts if t["status"] != "done"],
            ensure_ascii=False,
        )
    if tool == "add_task":
        t = taskstore.add_task(args.get("title", "untitled"), args.get("description", ""))
        return f"scheduled follow-up task {t['id']}"
    if tool == "complete_task":
        t = taskstore.update_task(args.get("id", ""), status="done", result=args.get("result", ""))
        return "task completed" if t else "task id not found"
    if tool == "finish":
        return "__finish__"
    return f"unknown tool: {tool}"


async def run_agent(goal: str, task: dict | None = None) -> AsyncIterator[dict]:
    """Execute a goal with a plan->act->verify loop, yielding step events."""
    import tasks as taskstore

    context = {
        "goal": goal,
        "task": task,
        "agenda": [{"id": t["id"], "title": t["title"], "status": t["status"],
                    "scheduled": t.get("scheduled"), "description": t.get("description", "")}
                   for t in taskstore.list_tasks() if t["status"] != "done"],
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Task to complete: {goal}\n\n"
            f"Current agenda: {json.dumps(context['agenda'], ensure_ascii=False)}\n\n"
            "First, decide on a short plan, then begin executing it one step at a "
            "time. Respond with your JSON action."
        )},
    ]

    if task:
        yield {"event": "start", "task": task}

    # Planning step
    plan_req = messages + [{"role": "user", "content":
                            "Before acting, list 2-5 concrete steps as JSON: "
                            '{"steps": ["...", "..."]}. Nothing else.'}]
    plan_text = await _chat(plan_req)
    steps = _extract_plan(plan_text)
    if steps:
        messages.append({"role": "assistant", "content": plan_text})
        yield {"event": "plan", "steps": steps}

    # Action loop
    for i in range(MAX_STEPS):
        response = await _chat(messages)
        messages.append({"role": "assistant", "content": response})
        parsed = _extract_json(response)

        if not parsed:
            yield {"event": "step", "index": i, "thought": response.strip()[:300],
                   "tool": None, "args": None, "observation": "could not parse a tool call; retrying"}
            messages.append({"role": "user", "content":
                             "That was not valid JSON with an action. Reply with ONLY the JSON object."})
            continue

        thought = parsed.get("thought", "")
        action = parsed.get("action", {}) or {}
        tool = action.get("tool")
        args = action.get("args", {}) or {}
        yield {"event": "step", "index": i, "thought": thought, "tool": tool, "args": args}

        observation = _execute_tool(action, context)
        if observation == "__finish__":
            summary = args.get("summary", thought or "completed")
            if task:
                taskstore.update_task(task["id"], status="done", result=summary)
            yield {"event": "done", "summary": summary}
            return

        yield {"event": "observation", "index": i, "tool": tool, "result": observation}
        messages.append({"role": "user", "content":
                         f"Observation: {observation}\nWhat is your next action? (JSON only)"})

    yield {"event": "done", "summary": f"reached step limit ({MAX_STEPS}) without finishing"}


def _extract_plan(text: str) -> list:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
        steps = obj.get("steps", []) if isinstance(obj, dict) else []
        if isinstance(steps, list):
            return [str(s) for s in steps][:5]
    except json.JSONDecodeError:
        return []
    return []


async def propose_next_steps() -> dict:
    """Analyse agenda + memory + conversation patterns and suggest next steps."""
    from main import get_memory_context, conversation_history
    import tasks as taskstore

    agenda = [{"id": t["id"], "title": t["title"], "status": t["status"],
               "scheduled": t.get("scheduled"), "description": t.get("description", "")}
              for t in taskstore.list_tasks() if t["status"] != "done"]
    recent = [m.get("content", "") for m in conversation_history[-6:]] if conversation_history else []
    memory = get_memory_context()

    prompt = (
        "You are observing a user's workflow. Based on their open tasks, their "
        "memory and their recent conversation, recognise the pattern of what they "
        "are working towards and propose the next logical step(s).\n\n"
        f"Open agenda:\n{json.dumps(agenda, ensure_ascii=False, indent=2)}\n\n"
        f"Memory:\n{memory or '(empty)'}\n\n"
        f"Recent conversation topics:\n{json.dumps(recent, ensure_ascii=False)}\n\n"
        "Respond with ONLY JSON: {\"suggestions\": [{\"title\": \"...\", "
        "\"reason\": \"why this is the next step\", \"description\": \"what to do\"}]}"
    )
    text = await _chat([{"role": "system", "content": "You propose the next logical step in a user's workflow. Output JSON only."},
                        {"role": "user", "content": prompt}])
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"suggestions": []}
    try:
        obj = json.loads(m.group(0))
        suggestions = obj.get("suggestions", []) if isinstance(obj, dict) else []
        if isinstance(suggestions, list):
            return {"suggestions": suggestions[:5]}
    except json.JSONDecodeError:
        return {"suggestions": []}
    return {"suggestions": []}
