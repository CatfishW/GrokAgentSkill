# GrokAgentSkill

An agent skill for calling the Grok API (OpenAI-compatible) hosted at `https://mc.agaii.org/grok`.

## Install

```bash
npx skills add https://github.com/CatfishW/GrokAgentSkill
```

## What this skill does

Teaches your AI agent how to:

- Call `grok-3`, `grok-3-fast`, `grok-3-mini`, `grok-3-mini-fast`, and vision models
- Use streaming and non-streaming chat completions
- Integrate via the `openai` Python SDK as a drop-in replacement
- Manage tokens via the admin API
- Troubleshoot common errors (429, 401, etc.)

## Quick start

```bash
export GROK_API_KEY=<your_app_key>
python scripts/grok_api.py chat "Hello, Grok!"
```

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Full skill instructions loaded by the agent |
| `scripts/grok_api.py` | Zero-dependency CLI helper script |
| `scripts/example_messages.json` | Example multi-turn conversation JSON |
